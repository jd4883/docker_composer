# **Docker Composer**
Docker Composer is a small helper script written in python that allows creation of docker stacks providing bare minimum information in a centralized yaml file. The yaml file should look something like this boilerplate code:

## **Sample Yaml Parameters:**
    # Any environmental variable can be set here which will always apply to each container. The value can be overriden by defining it again at the stack service level
    Defaults:
         Container Home:    <Home folder i.e. /nobody>         
         Time Zone:         <Time Zone i.e. America/Los_Angeles?
         Domain:            <domain name>
         Email:             <domain email>
         docker_version:    <desired default docker compose version i.e. 3.7>
        PGID:               <default container PGID>
        PUID:               <default container PUID>>
        # default network is backend
        # frontend is used for any containers that will be given a domain hostname
        # vpn currently has no functionality but I intend to have some containers use a network space that lives under openvpn. This flag is intended to differentiate the network stack for this case. 
        networks:
            frontend:       false
            vpn:            false
        # default tag I left as latest but can be reconfigured if desired
        tag:                latest
    Globals:
        # default network stacks, would need a bit of refactoring the jinja template if you wish to change my naming convention
        Networks:
            - Backend
            - Backend_VPN
            - Frontend
        Paths:
        Profile: ~/.bashrc
        SSH:     ~/.ssh
        Cleanup:
          - .idea
        # this is all custom scripts you wish to run when using the auto generated launch script. For my example I have 3 aliased scripts listed below which I have run automatically in the order provided for each setup script I generate.
        Scripts:
          - rebuild-symlinks
          - docker_prune
          - rebuild-docker-stacks
    Stack Group Name:
       Volumes:
        - <a list of all volumes that are external and used in the stack. Can be left as [] if not used>
       configs:
        # i believe this area requires a mapping but as stated in my notes I haven't had great results in testing and haven't really tuned this area.
       secrets:
        <secret name>:
            file:   <secret file path. If secrets are not used then please leave this field blank>
       <Stack Name>:
            <Service Name>:
                secrets:
                    - <(optional) - list of secrets defined in the stack group, can be left blank if not used or given a value of []>
                configs:
                    - <(optional) - list of configs defined in the stack group, can be left blank if not used or given a value of []*, NOTE: in testing this was a more problematic field to get working as desired. I have not had great testing results with this so use at your own risk. Feel free to make a PR if it gets put to use and works well>
                OAUTH_PROXY:        <(optional) - bool defaults false. If enabled oauth traefik code is generated>
                proxy_secrets:      <(optional) - bool defaults false, can be enabled to generate secret files for oauth. Can be used with or without oauth. This should be implicit with OAUTH enabled but I have not done heavy testing>
                subdomains:         <subdomain, currently a single subdomain but this can be refactored into a list pretty easily>
                tags:               <(optional) - the image tag if not latest>
                Image:              <the image to download for the given service, please define the tag in the above field or implicitly>
                ports:              
                    - <(optional), list of all port mappings, i.e. 80:80>
                Environment:
                    <(optional) - sub dictionary of envars for specific to a container>
                Volumes:
                    - <a list of volumes and their mapping i.e. $HOME:/home>                
                networks:
                    - <(optional) - list of network booleans to enable. Current options are frontend and vpn. If these are not needed please leave this blank or define any custom networks>
                Commands:     
                    - <(optional) list of commands to execute in order. I believe I got this working for a single command versus multiple directives but have not done a ton of testing>

Since I built this tool for personal use and don't anticipate a wide userbase, I kept it pretty simple and there are definitely ways to improve it. 
