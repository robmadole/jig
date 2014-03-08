# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = '2'

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box     = 'jig-development-vmware'
  config.vm.box_url = 'http://jig-base-boxes.s3-website-us-east-1.amazonaws.com/jig-development-vmware.box'

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
