from . import defop


@defop('sh', -1, 0.5)
def op_sh(aipl, *args, *kwargs):
    'Run the command described by args.  Return (retcode, stderr, stdout) columns.'
    import subprocess
    r = subprocess.run(args, text=True,
                       stdin=subprocess.PIPE,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    return dict(retcode=r.returncode,
                stderr=r.stderr,
                stdout=r.stdout)
