import httpx
from app.core.config import settings

class GitHubConnector:
    BASE='https://api.github.com'
    def _headers(self):
        h={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':settings.github_api_version}
        if settings.github_token: h['Authorization']=f'Bearer {settings.github_token}'
        return h
    def request(self,method,path,**kwargs):
        with httpx.Client(timeout=30,headers=self._headers()) as c:
            r=c.request(method,self.BASE+path,**kwargs)
        if r.status_code >= 400:
            raise RuntimeError(f'GitHub {r.status_code}: {r.text[:1000]}')
        if r.status_code==204: return {}
        return r.json()
    def me(self): return self.request('GET','/user')
    def repos(self,limit=50): return self.request('GET','/user/repos',params={'per_page':min(int(limit),100),'sort':'updated'})
    def repo(self,owner,repo): return self.request('GET',f'/repos/{owner}/{repo}')
    def workflow_runs(self,owner,repo,limit=20):
        return self.request('GET',f'/repos/{owner}/{repo}/actions/runs',params={'per_page':min(int(limit),100)}).get('workflow_runs',[])
