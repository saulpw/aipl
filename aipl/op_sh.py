from . import defop


@defop('sh', 0, 0.5)
def op_sh(aipl, stdin, *args):
    'Run the command described by args.  Return (retcode, stderr, stdout) columns.'
    import subprocess
    r = subprocess.run(args, text=True,
                       stdin=subprocess.PIPE,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    return dict(retcode=r.returncode,
                stdin=stdin,
                stderr=r.stderr,
                stdout=r.stdout)
