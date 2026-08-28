from pathlib import Path
import subprocess
from app.agents.base import BaseAgent
from app.core.models import RiskLevel
from app.connectors.github import GitHubConnector
from app.core.errors import NotConfiguredError

class DevelopmentAgent(BaseAgent):
    id='development';name='DevelopmentAgent';display_name='Development Agent';description='Git, GitHub, repositorios, tests, branches y workflows.';integration='github/local';requires_auth=False;capabilities=['Git','GitHub','tests','branches','workflows']
    ACTION_RISKS={'inspect_repo':RiskLevel.READ,'git_status':RiskLevel.READ,'github_repos':RiskLevel.READ,'workflow_runs':RiskLevel.READ,'list_branches':RiskLevel.READ,'run_tests':RiskLevel.PREPARE,'commit':RiskLevel.WRITE,'push':RiskLevel.WRITE,'delete_branch':RiskLevel.DANGEROUS}
    def _path(self,r):return Path(r.payload.get('path','.')).resolve()
    def _remote_is_github(self,path):
        p=subprocess.run(['git','-C',str(path),'remote','get-url','origin'],capture_output=True,text=True,timeout=20)
        return p.returncode==0 and 'github.com' in p.stdout.lower()
    def _require_github_if_remote(self,path):
        if self._remote_is_github(path):
            gh=GitHubConnector()
            if not gh.configured():raise NotConfiguredError('github')
            gh.me()  # validates token and permissions before GitHub-bound Git actions
    def handle(self,r,ctx):
        gh=GitHubConnector()
        if r.action=='github_repos':return {'repos':gh.repos(r.payload.get('limit',50))}
        if r.action=='workflow_runs':return {'runs':gh.workflow_runs(r.payload['owner'],r.payload['repo'],r.payload.get('limit',20))}
        if r.action=='list_branches':return {'branches':gh.branches(r.payload['owner'],r.payload['repo'],r.payload.get('limit',100))}
        if r.action=='delete_branch':return {'deleted':True,'result':gh.delete_branch(r.payload['owner'],r.payload['repo'],r.payload['branch'])}
        path=self._path(r)
        if r.action=='inspect_repo':
            if not path.exists():raise FileNotFoundError(path)
            return {'path':str(path),'items':[p.name for p in path.iterdir()][:250]}
        if r.action=='git_status':
            p=subprocess.run(['git','-C',str(path),'status','--short'],capture_output=True,text=True,timeout=30);return {'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
        if r.action=='run_tests':
            cmd=r.payload.get('command',['python','-m','pytest','-q'])
            if not isinstance(cmd,list):raise ValueError('command must be a list')
            p=subprocess.run(cmd,cwd=str(path),capture_output=True,text=True,timeout=min(int(r.payload.get('timeout',180)),900));return {'returncode':p.returncode,'stdout':p.stdout[-12000:],'stderr':p.stderr[-12000:]}
        if r.action=='commit':
            self._require_github_if_remote(path);p=subprocess.run(['git','-C',str(path),'commit','-m',r.payload['message']],capture_output=True,text=True,timeout=120);return {'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
        if r.action=='push':
            self._require_github_if_remote(path);p=subprocess.run(['git','-C',str(path),'push',r.payload.get('remote','origin'),r.payload.get('branch','HEAD')],capture_output=True,text=True,timeout=180);return {'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
        raise ValueError('Unsupported action')
