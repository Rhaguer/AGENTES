from __future__ import annotations
import threading
import uuid
from pathlib import Path
import httpx
from app.core.config import settings

GRAPH='https://graph.microsoft.com/v1.0'
TOKEN_CACHE=Path('data/ms_token_cache.json')

BASE_SCOPES=[
    'User.Read',
    'Mail.Read',
    'Mail.Send',
    'Calendars.ReadWrite',
    'Chat.Read',
    'Team.ReadBasic.All',
    'Channel.ReadBasic.All',
]
CHANNEL_SCOPE='ChannelMessage.Read.All'

_LOGIN_JOBS={}
_LOGIN_LOCK=threading.Lock()

class MicrosoftGraphConnector:
    def __init__(self):
        self.client_id=settings.ms_client_id
        self.tenant_id=settings.ms_tenant_id or 'organizations'

    def _msal(self):
        try:
            import msal
        except ImportError as e:
            raise RuntimeError('Falta dependencia msal. Ejecuta: pip install -r requirements.txt') from e
        return msal

    def _cache_and_app(self):
        if not self.client_id:
            raise RuntimeError('MS_CLIENT_ID no configurado en .env')
        msal=self._msal()
        cache=msal.SerializableTokenCache()
        if TOKEN_CACHE.exists():
            try:
                cache.deserialize(TOKEN_CACHE.read_text(encoding='utf-8'))
            except Exception:
                pass
        app=msal.PublicClientApplication(
            self.client_id,
            authority=f'https://login.microsoftonline.com/{self.tenant_id}',
            token_cache=cache,
        )
        return cache,app

    def scopes(self):
        scopes=list(BASE_SCOPES)
        if settings.ms_enable_teams_channels:
            scopes.append(CHANNEL_SCOPE)
        return scopes

    def _save_cache(self, cache):
        if cache.has_state_changed:
            TOKEN_CACHE.parent.mkdir(parents=True,exist_ok=True)
            TOKEN_CACHE.write_text(cache.serialize(),encoding='utf-8')

    def start_device_login(self):
        cache,app=self._cache_and_app()
        flow=app.initiate_device_flow(scopes=self.scopes())
        if 'user_code' not in flow:
            raise RuntimeError(f'No se pudo iniciar device flow: {flow}')

        job_id=uuid.uuid4().hex
        safe={
            'job_id': job_id,
            'status': 'pending',
            'message': flow.get('message',''),
            'user_code': flow.get('user_code'),
            'verification_uri': flow.get('verification_uri') or flow.get('verification_url'),
            'expires_in': flow.get('expires_in'),
        }
        with _LOGIN_LOCK:
            _LOGIN_JOBS[job_id]=dict(safe)

        def worker():
            try:
                result=app.acquire_token_by_device_flow(flow)
                self._save_cache(cache)
                if 'access_token' in result:
                    update={
                        'status':'authenticated',
                        'account':result.get('id_token_claims',{}).get('preferred_username'),
                    }
                else:
                    update={
                        'status':'error',
                        'error':result.get('error_description') or result.get('error') or str(result),
                    }
            except Exception as exc:
                update={'status':'error','error':str(exc)}
            with _LOGIN_LOCK:
                if job_id in _LOGIN_JOBS:
                    _LOGIN_JOBS[job_id].update(update)

        threading.Thread(target=worker,daemon=True,name=f'ms-device-login-{job_id[:8]}').start()
        return safe

    def device_login_status(self,job_id):
        with _LOGIN_LOCK:
            job=_LOGIN_JOBS.get(job_id)
            if not job:
                raise RuntimeError('job_id de autenticación no encontrado o expirado en este proceso.')
            return dict(job)

    # Compatibilidad con el endpoint anterior: ahora inicia y devuelve el código inmediatamente.
    def login_device_code(self):
        return self.start_device_login()

    def _token(self):
        cache,app=self._cache_and_app()
        accounts=app.get_accounts()
        result=None
        if accounts:
            result=app.acquire_token_silent(self.scopes(),account=accounts[0])
        self._save_cache(cache)
        if not result or 'access_token' not in result:
            raise RuntimeError('Microsoft no autenticado. Ejecuta /auth/microsoft/device-login primero.')
        return result['access_token']

    def request(self,method,path,*,params=None,json_body=None):
        token=self._token()
        with httpx.Client(timeout=30) as c:
            r=c.request(method,f'{GRAPH}{path}',params=params,json=json_body,
                        headers={'Authorization':f'Bearer {token}','Accept':'application/json'})
        if r.status_code >= 400:
            raise RuntimeError(f'Microsoft Graph {r.status_code}: {r.text[:1000]}')
        if r.status_code == 204 or not r.content:
            return {}
        return r.json()

    def me(self):
        return self.request('GET','/me')

    def unread_mail(self,limit=20):
        params={'$filter':'isRead eq false','$top':str(min(int(limit),50)),
                '$select':'id,subject,from,receivedDateTime,isRead,webLink,bodyPreview'}
        return self.request('GET','/me/messages',params=params).get('value',[])

    def send_mail(self,to,subject,body):
        msg={'message':{'subject':subject,'body':{'contentType':'Text','content':body},
                        'toRecipients':[{'emailAddress':{'address':addr}} for addr in to]},
             'saveToSentItems':True}
        return self.request('POST','/me/sendMail',json_body=msg)

    def calendar_events(self,start_iso,end_iso,limit=50):
        params={'startDateTime':start_iso,'endDateTime':end_iso,'$top':str(min(int(limit),100)),
                '$select':'id,subject,start,end,location,organizer,attendees,webLink,isOnlineMeeting,onlineMeeting'}
        return self.request('GET','/me/calendarView',params=params).get('value',[])

    def create_event(self,subject,start_iso,end_iso,timezone='America/Santiago',attendees=None,body=''):
        payload={'subject':subject,'start':{'dateTime':start_iso,'timeZone':timezone},
                 'end':{'dateTime':end_iso,'timeZone':timezone},
                 'body':{'contentType':'Text','content':body}}
        if attendees:
            payload['attendees']=[{'emailAddress':{'address':a},'type':'required'} for a in attendees]
        return self.request('POST','/me/events',json_body=payload)

    def chats(self,limit=30):
        return self.request('GET','/me/chats',params={'$top':str(min(int(limit),50))}).get('value',[])

    def chat_messages(self,chat_id,limit=50):
        return self.request('GET',f'/chats/{chat_id}/messages',params={'$top':str(min(int(limit),50))}).get('value',[])

    def joined_teams(self):
        return self.request('GET','/me/joinedTeams').get('value',[])

    def channels(self,team_id):
        return self.request('GET',f'/teams/{team_id}/channels').get('value',[])

    def channel_messages(self,team_id,channel_id,limit=50):
        if not settings.ms_enable_teams_channels:
            raise RuntimeError('MS_ENABLE_TEAMS_CHANNELS=false. Habilítalo solo después de conceder ChannelMessage.Read.All.')
        return self.request('GET',f'/teams/{team_id}/channels/{channel_id}/messages',params={'$top':str(min(int(limit),50))}).get('value',[])
