# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = '2'

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = 'robmadole/jig-development'

  # Use a private network so NFS can do its thing
  config.vm.network "private_network", type: "dhcp"

  # Disable the default share
  config.vm.synced_folder '.', '/vagrant', disabled: true
  # Use the name of the project
  config.vm.synced_folder '.', '/jig', type: 'nfs'
  # Configured for Salt
  config.vm.synced_folder 'salt/roots/', '/srv', type: 'nfs'

  # Documentation
  config.vm.network 'forwarded_port', guest: 5001, host: 5001

  config.vm.provision :salt do |salt|
    salt.minion_config = 'salt/minion'
    salt.run_highstate = true
    salt.install_type  = 'git'
    salt.install_args  = 'v2014.1.13'
  end
end
