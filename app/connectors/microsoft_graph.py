from __future__ import annotations
import json, threading, uuid
from pathlib import Path
import httpx
from app.core.config import settings
from app.core.errors import AuthenticationRequiredError, NotConfiguredError, ProviderRateLimitError, ProviderUnavailableError, AppError
from app.core.integration import IntegrationConnector
from app.core.resilience import retry_call
from app.core.secrets import secret_store

GRAPH='https://graph.microsoft.com/v1.0'
TOKEN_CACHE_PATH=Path('data/ms_token_cache.enc')
_LOGIN_JOBS={};_LOGIN_LOCK=threading.Lock()

class MicrosoftGraphConnector(IntegrationConnector):
    provider='microsoft'
    capabilities=['outlook_mail','outlook_calendar','teams_chat','teams','channels']
    def __init__(self):
        self.client_id=settings.ms_client_id
        self.tenant_id=settings.ms_tenant_id

    def configured(self):return bool(self.client_id and self.tenant_id)
    def _msal(self):
        try:import msal;return msal
        except ImportError as e:raise ProviderUnavailableError('microsoft','Missing msal dependency') from e
    def scopes(self):
        scopes=[x for x in settings.ms_scopes.split() if x]
        if settings.ms_enable_teams_channels and 'ChannelMessage.Read.All' not in scopes:scopes.append('ChannelMessage.Read.All')
        return scopes
    def _cache_app(self):
        if not self.configured():raise NotConfiguredError('microsoft')
        msal=self._msal();cache=msal.SerializableTokenCache();raw=secret_store.read_text(TOKEN_CACHE_PATH)
        if raw:
            try:cache.deserialize(raw)
            except Exception:pass
        app=msal.PublicClientApplication(self.client_id,authority=f'https://login.microsoftonline.com/{self.tenant_id}',token_cache=cache)
        return cache,app
    def _save(self,cache):
        if cache.has_state_changed:secret_store.write_text(TOKEN_CACHE_PATH,cache.serialize())
    def authenticated(self):
        if not self.configured():return False
        try:
            cache,app=self._cache_app();accounts=app.get_accounts()
            if not accounts:return False
            result=app.acquire_token_silent(self.scopes(),account=accounts[0]);self._save(cache)
            return bool(result and result.get('access_token'))
        except Exception:return False
    def disconnect(self):secret_store.delete(TOKEN_CACHE_PATH);return {'disconnected':True}
    def start_device_login(self):
        cache,app=self._cache_app();flow=app.initiate_device_flow(scopes=self.scopes())
        if 'user_code' not in flow:raise AppError('MICROSOFT_DEVICE_FLOW_FAILED','Could not initialize Microsoft device code flow',424,{'provider_error':flow.get('error')})
        job_id=uuid.uuid4().hex
        safe={'job_id':job_id,'status':'pending','message':flow.get('message',''),'user_code':flow.get('user_code'),
              'verification_uri':flow.get('verification_uri') or flow.get('verification_url'),'expires_in':flow.get('expires_in')}
        with _LOGIN_LOCK:_LOGIN_JOBS[job_id]=dict(safe)
        def worker():
            try:
                result=app.acquire_token_by_device_flow(flow);self._save(cache)
                if result.get('access_token'):update={'status':'authenticated','account':result.get('id_token_claims',{}).get('preferred_username')}
                else:update={'status':'error','error_code':result.get('error'),'error':result.get('error_description') or 'Authentication failed'}
            except Exception as exc:update={'status':'error','error':str(exc)[:500]}
            with _LOGIN_LOCK:
                if job_id in _LOGIN_JOBS:_LOGIN_JOBS[job_id].update(update)
        threading.Thread(target=worker,daemon=True,name=f'ms-login-{job_id[:8]}').start();return safe
    def device_login_status(self,job_id):
        with _LOGIN_LOCK:job=_LOGIN_JOBS.get(job_id)
        if not job:raise AppError('MICROSOFT_LOGIN_JOB_NOT_FOUND','Microsoft authentication job not found',404)
        return dict(job)
    def _token(self):
        cache,app=self._cache_app();accounts=app.get_accounts()
        if not accounts:raise AuthenticationRequiredError('microsoft')
        result=app.acquire_token_silent(self.scopes(),account=accounts[0]);self._save(cache)
        if not result or not result.get('access_token'):
            if result and result.get('error')=='invalid_grant':self.disconnect()
            raise AuthenticationRequiredError('microsoft')
        return result['access_token']
    def request(self,method,path,*,params=None,json_body=None):
        token=self._token()
        def do():
            try:
                with httpx.Client(timeout=settings.provider_timeout_seconds) as client:
                    r=client.request(method,GRAPH+path,params=params,json=json_body,headers={'Authorization':f'Bearer {token}','Accept':'application/json'})
            except httpx.HTTPError as e:raise ProviderUnavailableError('microsoft',str(e)) from e
            if r.status_code==429:raise ProviderRateLimitError('microsoft')
            if r.status_code in (401,403):raise AppError('MICROSOFT_AUTHORIZATION_FAILED','Microsoft Graph rejected the current authorization',401 if r.status_code==401 else 403)
            if r.status_code>=500:raise ProviderUnavailableError('microsoft',f'Microsoft Graph returned {r.status_code}')
            if r.status_code>=400:raise AppError('MICROSOFT_GRAPH_ERROR',f'Microsoft Graph returned {r.status_code}',424,{'status':r.status_code})
            return {} if r.status_code==204 or not r.content else r.json()
        return retry_call('microsoft',do)
    def me(self):return self.request('GET','/me',params={'$select':'id,displayName,userPrincipalName,mail'})
    def unread_mail(self,limit=20):
        return self.request('GET','/me/messages',params={'$filter':'isRead eq false','$top':str(min(int(limit),50)),'$select':'id,subject,from,receivedDateTime,isRead,webLink,bodyPreview'}).get('value',[])
    def send_mail(self,to,subject,body):
        payload={'message':{'subject':subject,'body':{'contentType':'Text','content':body},'toRecipients':[{'emailAddress':{'address':a}} for a in to]},'saveToSentItems':True}
        return self.request('POST','/me/sendMail',json_body=payload)
    def calendar_events(self,start_iso,end_iso,limit=50):
        return self.request('GET','/me/calendarView',params={'startDateTime':start_iso,'endDateTime':end_iso,'$top':str(min(int(limit),100)),'$select':'id,subject,start,end,location,organizer,attendees,webLink,isOnlineMeeting'}).get('value',[])
    def create_event(self,subject,start_iso,end_iso,timezone='America/Santiago',attendees=None,body=''):
        payload={'subject':subject,'start':{'dateTime':start_iso,'timeZone':timezone},'end':{'dateTime':end_iso,'timeZone':timezone},'body':{'contentType':'Text','content':body}}
        if attendees:payload['attendees']=[{'emailAddress':{'address':a},'type':'required'} for a in attendees]
        return self.request('POST','/me/events',json_body=payload)
    def chats(self,limit=30):return self.request('GET','/me/chats',params={'$top':str(min(int(limit),50))}).get('value',[])
    def chat_messages(self,chat_id,limit=50):return self.request('GET',f'/chats/{chat_id}/messages',params={'$top':str(min(int(limit),50))}).get('value',[])
    def joined_teams(self):return self.request('GET','/me/joinedTeams').get('value',[])
    def channels(self,team_id):return self.request('GET',f'/teams/{team_id}/channels').get('value',[])
    def channel_messages(self,team_id,channel_id,limit=50):
        if not settings.ms_enable_teams_channels:raise AppError('TEAMS_CHANNEL_MESSAGES_DISABLED','Enable MS_ENABLE_TEAMS_CHANNELS only after admin consent for ChannelMessage.Read.All',503)
        return self.request('GET',f'/teams/{team_id}/channels/{channel_id}/messages',params={'$top':str(min(int(limit),50))}).get('value',[])
