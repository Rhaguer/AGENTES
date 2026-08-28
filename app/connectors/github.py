from __future__ import annotations
import httpx
from pathlib import Path
from app.core.config import settings
from app.core.errors import AuthenticationRequiredError, NotConfiguredError, ProviderRateLimitError, ProviderUnavailableError, AppError
from app.core.integration import IntegrationConnector
from app.core.resilience import retry_call

class GitHubConnector(IntegrationConnector):
    provider='github';capabilities=['repositories','workflows','branches']
    BASE='https://api.github.com';DISABLED=Path('data/github.disabled')
    def configured(self):return bool(settings.github_token)
    def enabled(self):return not self.DISABLED.exists()
    def connect(self):
        if self.DISABLED.exists():self.DISABLED.unlink()
        return self.me()
    def disconnect(self):
        self.DISABLED.parent.mkdir(parents=True,exist_ok=True);self.DISABLED.write_text('disabled',encoding='utf-8');return {'disconnected':True}

    def _headers(self):
        if not self.configured():raise NotConfiguredError('github')
        if not self.enabled():raise AuthenticationRequiredError('github')
        return {'Authorization':f'Bearer {settings.github_token}','Accept':'application/vnd.github+json','X-GitHub-Api-Version':settings.github_api_version}
    def request(self,method,path,**kwargs):
        def do():
            try:
                with httpx.Client(timeout=settings.provider_timeout_seconds,headers=self._headers()) as c:r=c.request(method,self.BASE+path,**kwargs)
            except httpx.HTTPError as e:raise ProviderUnavailableError('github',str(e)) from e
            if r.status_code==429 or (r.status_code==403 and r.headers.get('x-ratelimit-remaining')=='0'):raise ProviderRateLimitError('github')
            if r.status_code==401:raise AuthenticationRequiredError('github')
            if r.status_code==403:raise AppError('GITHUB_FORBIDDEN','GitHub token does not have the required permission',403)
            if r.status_code>=500:raise ProviderUnavailableError('github',f'GitHub returned {r.status_code}')
            if r.status_code>=400:raise AppError('GITHUB_API_ERROR',f'GitHub returned {r.status_code}',424,{'status':r.status_code})
            return {} if r.status_code==204 or not r.content else r.json()
        return retry_call('github',do)
    def authenticated(self):
        if not self.configured() or not self.enabled():return False
        try:self.me();return True
        except Exception:return False
    def me(self):return self.request('GET','/user')
    def repos(self,limit=50):return self.request('GET','/user/repos',params={'per_page':min(int(limit),100),'sort':'updated'})
    def repo(self,owner,repo):return self.request('GET',f'/repos/{owner}/{repo}')
    def workflow_runs(self,owner,repo,limit=20):return self.request('GET',f'/repos/{owner}/{repo}/actions/runs',params={'per_page':min(int(limit),100)}).get('workflow_runs',[])
    def branches(self,owner,repo,limit=100):return self.request('GET',f'/repos/{owner}/{repo}/branches',params={'per_page':min(int(limit),100)})
    def delete_branch(self,owner,repo,branch):return self.request('DELETE',f'/repos/{owner}/{repo}/git/refs/heads/{branch}')
