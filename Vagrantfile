# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = '2'

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box     = 'robmadole/jig-development'

  config.vm.synced_folder '.', '/vagrant', type: 'nfs'
  config.vm.synced_folder 'salt/roots/', '/srv', type: 'nfs'

  # Documentation
  config.vm.network 'forwarded_port', guest: 5001, host: 5001

  config.vm.provision :salt do |salt|
    salt.minion_config = 'salt/minion'
    salt.run_highstate = true
    salt.install_type  = 'git'
    salt.install_args  = 'v2014.1.0'
  end
end
