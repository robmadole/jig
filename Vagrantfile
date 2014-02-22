# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = '2'

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box     = 'raring-vmware'
  config.vm.box_url = 'https://s3.amazonaws.com/life360-vagrant/raring64.box'

  config.vm.synced_folder 'salt/roots/', '/srv'

  # Documentation
  config.vm.network 'forwarded_port', guest: 5001, host: 5001

  config.vm.provision :salt do |salt|
    salt.minion_config = 'salt/minion'
    salt.run_highstate = true
    salt.install_type  = 'git'
    salt.install_args  = 'v0.17.5'
  end
end
