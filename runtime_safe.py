"""Avoid a hanging optional Windows WMI platform probe; no package edits."""
import platform,runpy,sys,os
def unavailable(*args,**kwargs):raise OSError('WMI probe unavailable in this session')
if os.name=='nt' and hasattr(platform,'_wmi_query'):platform._wmi_query=unavailable
platform.machine=lambda:os.environ.get('PROCESSOR_ARCHITECTURE','AMD64')
platform.processor=lambda:os.environ.get('PROCESSOR_IDENTIFIER','')
# No platform-system override: this wrapper also works on non-Windows hosts.
target=sys.argv.pop(1)
sys.argv[0]=target
runpy.run_path(target,run_name='__main__')
