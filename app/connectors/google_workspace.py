from __future__ import annotations
import base64
from email.message import EmailMessage
from pathlib import Path
from app.core.config import settings

SCOPES=[
 'https://www.googleapis.com/auth/gmail.readonly',
 'https://www.googleapis.com/auth/gmail.send',
 'https://www.googleapis.com/auth/calendar.readonly',
 'https://www.googleapis.com/auth/calendar.events',
]

class GoogleWorkspaceConnector:
    def _imports(self):
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError as e:
            raise RuntimeError('Faltan dependencias Google. Ejecuta: pip install -r requirements.txt') from e
        return Request,Credentials,InstalledAppFlow,build

    def _credentials(self,interactive=False):
        Request,Credentials,InstalledAppFlow,_=self._imports()
        token=Path(settings.google_token_file)
        credfile=Path(settings.google_credentials_file)
        creds=None
        if token.exists():
            try: creds=Credentials.from_authorized_user_file(str(token),SCOPES)
            except Exception: creds=None
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        if (not creds or not creds.valid) and interactive:
            if not credfile.exists():
                raise RuntimeError(f'No existe {credfile}. Descarga el OAuth Desktop Client JSON desde Google Cloud.')
            flow=InstalledAppFlow.from_client_secrets_file(str(credfile),SCOPES)
            creds=flow.run_local_server(port=0)
        if not creds or not creds.valid:
            raise RuntimeError('Google no autenticado. Ejecuta /auth/google/login primero.')
        token.parent.mkdir(parents=True,exist_ok=True)
        token.write_text(creds.to_json(),encoding='utf-8')
        return creds

    def login(self):
        creds=self._credentials(interactive=True)
        return {'authenticated': bool(creds and creds.valid)}

    def _service(self,name,version):
        *_,build=self._imports()
        return build(name,version,credentials=self._credentials(),cache_discovery=False)

    def unread_mail(self,limit=20):
        svc=self._service('gmail','v1')
        listing=svc.users().messages().list(userId='me',q='is:unread',maxResults=min(int(limit),100)).execute()
        out=[]
        for item in listing.get('messages',[]):
            msg=svc.users().messages().get(userId='me',id=item['id'],format='metadata',
                metadataHeaders=['Subject','From','Date']).execute()
            headers={h['name'].lower():h['value'] for h in msg.get('payload',{}).get('headers',[])}
            out.append({'id':msg.get('id'),'threadId':msg.get('threadId'),'subject':headers.get('subject',''),
                        'from':headers.get('from',''),'date':headers.get('date',''),'snippet':msg.get('snippet','')})
        return out

    def send_mail(self,to,subject,body):
        msg=EmailMessage(); msg.set_content(body); msg['To']=', '.join(to); msg['Subject']=subject
        raw=base64.urlsafe_b64encode(msg.as_bytes()).decode()
        return self._service('gmail','v1').users().messages().send(userId='me',body={'raw':raw}).execute()

    def calendar_events(self,time_min,time_max,limit=50):
        result=self._service('calendar','v3').events().list(calendarId='primary',timeMin=time_min,timeMax=time_max,
              maxResults=min(int(limit),100),singleEvents=True,orderBy='startTime').execute()
        return result.get('items',[])

    def create_event(self,summary,start_iso,end_iso,timezone='America/Santiago',attendees=None,description=''):
        body={'summary':summary,'description':description,
              'start':{'dateTime':start_iso,'timeZone':timezone},
              'end':{'dateTime':end_iso,'timeZone':timezone}}
        if attendees: body['attendees']=[{'email':a} for a in attendees]
        return self._service('calendar','v3').events().insert(calendarId='primary',body=body,sendUpdates='all').execute()

    def me(self):
        return self._service('gmail','v1').users().getProfile(userId='me').execute()
