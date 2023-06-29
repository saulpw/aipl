from aipl import defop, Table


@defop('sh', 0, 1.5)
def op_sh(aipl, cmdline:str, **kwargs) -> dict:
    'Run the command described by args.  Return (retcode, stderr, stdout) columns.'
    import subprocess
    r = subprocess.run(cmdline, shell=True, text=True,
#                       stdin=subprocess.PIPE,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    return Table([dict(retcode=r.returncode,
                stderr=r.stderr,
                stdout=r.stdout)])

@defop('shtty', None, 0.5)
def op_shtty(aipl, _:'LazyRow', *args) -> dict:
    'Run the command described by args.  Return (retcode, stderr, stdout) columns.'
    import subprocess
    r = subprocess.run(args, text=True,
                       stderr=subprocess.PIPE)
    return dict(retcode=r.returncode,
                stderr=r.stderr)
