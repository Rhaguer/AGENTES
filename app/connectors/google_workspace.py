from __future__ import annotations
import base64,json,secrets
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import urlparse
from app.core.config import settings
from app.core.errors import AuthenticationRequiredError, NotConfiguredError, ProviderUnavailableError, AppError
from app.core.integration import IntegrationConnector
from app.core.resilience import retry_call
from app.core.errors import ProviderRateLimitError
from app.core.secrets import secret_store

SCOPES=['https://www.googleapis.com/auth/gmail.readonly','https://www.googleapis.com/auth/gmail.send','https://www.googleapis.com/auth/calendar.readonly','https://www.googleapis.com/auth/calendar.events']
TOKEN_PATH=Path('data/google_token.enc');_OAUTH_STATES={}

class GoogleWorkspaceConnector(IntegrationConnector):
    provider='google';capabilities=['gmail','calendar']
    def _imports(self):
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import Flow
            from googleapiclient.discovery import build
            return Request,Credentials,Flow,build
        except ImportError as e:raise ProviderUnavailableError('google','Missing Google API dependencies') from e
    def _credentials_file(self):return Path(settings.google_credentials_file)
    def configured(self):
        p=self._credentials_file()
        if not p.exists():return False
        try:
            data=json.loads(p.read_text(encoding='utf-8'));node=data.get('installed') or data.get('web')
            return bool(node and node.get('client_id') and node.get('auth_uri') and node.get('token_uri'))
        except Exception:return False
    def _load_credentials(self):
        if not self.configured():raise NotConfiguredError('google')
        Request,Credentials,_,_=self._imports();raw=secret_store.read_text(TOKEN_PATH)
        if not raw:raise AuthenticationRequiredError('google')
        try:info=json.loads(raw);creds=Credentials.from_authorized_user_info(info,SCOPES)
        except Exception:raise AuthenticationRequiredError('google')
        if creds.expired and creds.refresh_token:
            try:creds.refresh(Request());secret_store.write_text(TOKEN_PATH,creds.to_json())
            except Exception:
                secret_store.delete(TOKEN_PATH);raise AuthenticationRequiredError('google')
        if not creds.valid:raise AuthenticationRequiredError('google')
        granted=set(creds.scopes or [])
        if not set(SCOPES).issubset(granted):raise AppError('GOOGLE_SCOPE_MISMATCH','Stored Google token does not contain all required scopes',401)
        return creds
    def authenticated(self):
        try:self._load_credentials();return True
        except Exception:return False
    def start_login(self):
        if not self.configured():raise NotConfiguredError('google')
        _,_,Flow,_=self._imports();flow=Flow.from_client_secrets_file(str(self._credentials_file()),scopes=SCOPES,redirect_uri=settings.google_redirect_uri)
        state=secrets.token_urlsafe(24);url,_=flow.authorization_url(access_type='offline',include_granted_scopes='true',prompt='consent',state=state)
        _OAUTH_STATES[state]=True
        return {'authorization_url':url,'state':state,'redirect_uri':settings.google_redirect_uri}
    def finish_login(self,state,code):
        if not _OAUTH_STATES.pop(state,None):raise AppError('GOOGLE_OAUTH_STATE_INVALID','Google OAuth state is invalid or expired',400)
        _,_,Flow,_=self._imports();flow=Flow.from_client_secrets_file(str(self._credentials_file()),scopes=SCOPES,state=state,redirect_uri=settings.google_redirect_uri)
        try:flow.fetch_token(code=code)
        except Exception as e:raise AppError('GOOGLE_OAUTH_FAILED','Google OAuth token exchange failed',424) from e
        secret_store.write_text(TOKEN_PATH,flow.credentials.to_json());return {'authenticated':True}
    def disconnect(self):secret_store.delete(TOKEN_PATH);return {'disconnected':True}
    def _service(self,name,version):
        *_,build=self._imports()
        try:return build(name,version,credentials=self._load_credentials(),cache_discovery=False)
        except AuthenticationRequiredError:raise
        except Exception as e:raise ProviderUnavailableError('google',str(e)[:500]) from e

    def _execute(self, request):
        def do():
            try:
                return request.execute(num_retries=0)
            except Exception as exc:
                status=getattr(getattr(exc,'resp',None),'status',None)
                if status==429:raise ProviderRateLimitError('google')
                if status in (401,403):raise AppError('GOOGLE_AUTHORIZATION_FAILED','Google API rejected the current authorization',401 if status==401 else 403)
                if status and status>=500:raise ProviderUnavailableError('google',f'Google API returned {status}')
                if status and status>=400:raise AppError('GOOGLE_API_ERROR',f'Google API returned {status}',424,{'status':status})
                raise ProviderUnavailableError('google',str(exc)[:500])
        return retry_call('google',do)

    def unread_mail(self,limit=20):
        svc=self._service('gmail','v1');listing=self._execute(svc.users().messages().list(userId='me',q='is:unread',maxResults=min(int(limit),100)));out=[]
        for item in listing.get('messages',[]):
            msg=self._execute(svc.users().messages().get(userId='me',id=item['id'],format='metadata',metadataHeaders=['Subject','From','Date']));headers={h['name'].lower():h['value'] for h in msg.get('payload',{}).get('headers',[])}
            out.append({'id':msg.get('id'),'threadId':msg.get('threadId'),'subject':headers.get('subject',''),'from':headers.get('from',''),'date':headers.get('date',''),'snippet':msg.get('snippet','')})
        return out
    def send_mail(self,to,subject,body):
        msg=EmailMessage();msg.set_content(body);msg['To']=', '.join(to);msg['Subject']=subject;raw=base64.urlsafe_b64encode(msg.as_bytes()).decode()
        svc=self._service('gmail','v1');return self._execute(svc.users().messages().send(userId='me',body={'raw':raw}))
    def calendar_events(self,time_min,time_max,limit=50):
        svc=self._service('calendar','v3');return self._execute(svc.events().list(calendarId='primary',timeMin=time_min,timeMax=time_max,maxResults=min(int(limit),100),singleEvents=True,orderBy='startTime')).get('items',[])
    def create_event(self,summary,start_iso,end_iso,timezone='America/Santiago',attendees=None,description=''):
        body={'summary':summary,'description':description,'start':{'dateTime':start_iso,'timeZone':timezone},'end':{'dateTime':end_iso,'timeZone':timezone}}
        if attendees:body['attendees']=[{'email':a} for a in attendees]
        svc=self._service('calendar','v3');return self._execute(svc.events().insert(calendarId='primary',body=body,sendUpdates='all'))
    def me(self):
        svc=self._service('gmail','v1');return self._execute(svc.users().getProfile(userId='me'))
