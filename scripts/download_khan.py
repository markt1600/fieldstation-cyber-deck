"""Resume the English Khan Academy collection, starting with a small usable sample."""
import os
from pathlib import Path
import subprocess
HOME=Path('/media/library/Education/Kolibri')
EXE=Path.home()/'fieldstation-kolibri/bin/kolibri'
CHANNEL='c9d7f950ab6b5a1199e3d6c10d7f0103'
if not os.path.ismount('/media/library'):raise SystemExit('SSD is not mounted.')
env=dict(os.environ,KOLIBRI_HOME=str(HOME))
# Download a video and an interactive exercise first so the viewer can be checked.
subprocess.run([str(EXE),'manage','importcontent','--node_ids','bc3ac45347f3556ba8169b59ae452b01,a54ad8cc9e4256c3a39fc7bfa35a93e6','network',CHANNEL],env=env,check=True)
subprocess.run([str(EXE),'manage','importcontent','--fail-on-error','network',CHANNEL],env=env,check=True)
(HOME/'download-complete').write_text('English Khan Academy import completed.\n')
