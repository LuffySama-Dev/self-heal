"""Pattern-based review of nonignored Git files and reachable historical blobs.

Reports locations/category only, never matched credential text. This complements
manual review; it is not proof of absence of every possible secret.
"""
import pathlib,re,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]

def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args])

def public_files():
    return sorted(set(p.decode() for p in git('ls-files','--cached','--others','--exclude-standard','-z').split(b'\0') if p))

PATTERNS={
 'private-key':rb'-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----',
 'github-token':rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b',
 'provider-token':rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b',
 'aws-access-id':rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
 'jwt':rb'\beyJ[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\b',
 'credential-in-url':rb'https?://[^\s/"<>:]+:[^\s/"<>]+@',
 'personal-home':rb'/(?:home|Users)/[A-Za-z0-9_.-]+/',
 'private-ip':rb'\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}|100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])(?:\.\d{1,3}){2})\b',
 'operational-session-id':rb'\b20\d{6}_\d{6}_[a-f0-9]{8}\b',
 'service-account-email':rb'[\w.+-]+@signozserviceaccount\.com',
}

def findings(label,data):
    output=[]
    for name,pattern in PATTERNS.items():
        for match in re.finditer(pattern,data):
            output.append(f'{label}:{data[:match.start()].count(bytes([10]))+1}: {name}')
    return output

def main():
    found=[];files=public_files()
    for name in files:
        p=ROOT/name
        if not p.is_file():continue
        if p.name in ['auth.json','credentials.json','.env'] or p.suffix in ['.db','.sqlite','.sqlite3','.pem','.key']:
            found.append(name+': forbidden public file type')
        found+=findings(name,p.read_bytes())
    # Scan reachable blobs, including files removed in a later commit.
    blobs={}
    for commit in git('rev-list','--all').decode().splitlines():
        for entry in git('ls-tree','-r','-z',commit).split(b'\0'):
            if not entry:continue
            meta,name=entry.split(b'\t',1);_,kind,oid=meta.split()
            if kind==b'blob':blobs.setdefault(oid.decode(),name.decode())
    for oid,name in blobs.items():found+=findings('history:'+name,git('cat-file','blob',oid))
    remotes=subprocess.run(['git','-C',str(ROOT),'config','--get-regexp',r'remote\..*\.url'],capture_output=True).stdout
    found+=findings('git-remotes',remotes)
    if found:
        print('\n'.join(found));raise SystemExit(1)
    print(f'PASS: {len(files)} public candidate files, {len(blobs)} historical blobs; no configured secret/private-data patterns found.')
if __name__=='__main__':main()
