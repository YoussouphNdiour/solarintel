import os                                                                                                                                                 
STACKS=['/root/dsb','/root/solarig','/root/odoo-two','/root/odoo-19-as-shafi-minhn92','/root/odoo-formation','/root/makine','/root/infosits','/root/aig'] 
for stack in STACKS:                                                                                                                                      
    path=os.path.join(stack,'docker-compose.yml')                                                                                                         
    if not os.path.exists(path):
        print('SKIP: '+path); continue
    content=open(path).read()
    if 'nginx_default' in content:
        print('DEJA PATCHE: '+path); continue
    lines=content.split('\n')
    last_restart=max(i for i,l in enumerate(lines) if '    restart: always' in l)
    lines.insert(last_restart+1,'    networks:')
    lines.insert(last_restart+2,'      - nginx_default')
    new_content='\n'.join(lines).rstrip()+'\n\nnetworks:\n  nginx_default:\n    external: true\n'
    open(path,'w').write(new_content)
    print('PATCHE: '+path)