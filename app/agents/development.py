from pathlib import Path
import subprocess
from app.agents.base import BaseAgent
from app.core.models import AgentResult,RiskLevel
from app.connectors.github import GitHubConnector

class DevelopmentAgent(BaseAgent):
    name='DevelopmentAgent'
    ACTION_RISKS={'inspect_repo':RiskLevel.READ,'git_status':RiskLevel.READ,'github_repos':RiskLevel.READ,'workflow_runs':RiskLevel.READ,'run_tests':RiskLevel.PREPARE,'commit':RiskLevel.WRITE,'push':RiskLevel.WRITE,'delete_branch':RiskLevel.DANGEROUS}
    def handle(self,r):
        if r.action=='github_repos':
            data=GitHubConnector().repos(r.payload.get('limit',50))
            return AgentResult(agent=self.name,action=r.action,ok=True,message=f'{len(data)} repositorios obtenidos.',data={'repos':data})
        if r.action=='workflow_runs':
            data=GitHubConnector().workflow_runs(r.payload['owner'],r.payload['repo'],r.payload.get('limit',20))
            return AgentResult(agent=self.name,action=r.action,ok=True,message='Workflows obtenidos.',data={'runs':data})
        path=Path(r.payload.get('path','.')).resolve()
        if r.action=='inspect_repo':
            if not path.exists(): return AgentResult(agent=self.name,action=r.action,ok=False,message='Ruta no encontrada.')
            return AgentResult(agent=self.name,action=r.action,ok=True,message='Repositorio inspeccionado.',data={'path':str(path),'items':[p.name for p in path.iterdir()][:200]})
        if r.action=='git_status':
            p=subprocess.run(['git','-C',str(path),'status','--short'],capture_output=True,text=True,timeout=30)
            return AgentResult(agent=self.name,action=r.action,ok=p.returncode==0,message='git status ejecutado.',data={'stdout':p.stdout,'stderr':p.stderr})
        if r.action=='run_tests':
            cmd=r.payload.get('command',['python','-m','pytest','-q'])
            if not isinstance(cmd,list): return AgentResult(agent=self.name,action=r.action,ok=False,message='command debe ser una lista de argumentos.')
            p=subprocess.run(cmd,cwd=str(path),capture_output=True,text=True,timeout=min(int(r.payload.get('timeout',120)),600))
            return AgentResult(agent=self.name,action=r.action,ok=p.returncode==0,message='Tests ejecutados.',data={'returncode':p.returncode,'stdout':p.stdout[-10000:],'stderr':p.stderr[-10000:]})
        if r.action in {'commit','push'}:
            args=['git','-C',str(path)] + (['commit','-m',r.payload['message']] if r.action=='commit' else ['push'])
            p=subprocess.run(args,capture_output=True,text=True,timeout=120)
            return AgentResult(agent=self.name,action=r.action,ok=p.returncode==0,message=f'{r.action} ejecutado.',data={'stdout':p.stdout,'stderr':p.stderr})
        return AgentResult(agent=self.name,action=r.action,ok=False,message='Acción no soportada.')
