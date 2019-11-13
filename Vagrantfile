# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"
DEFAULT_VB = "bento/ubuntu-18.04"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  # vagrant dns; requires `vagrant plugin install landrush`
  config.landrush.enabled = true
  config.landrush.tld = "vm"

  # artillery node
  config.vm.define "artillery" do |artillery|
    artillery.vm.box = DEFAULT_VB
    artillery.vm.hostname = "artillery.vm"
    artillery.vm.network "private_network", ip: "10.45.0.11"

    artillery.ssh.forward_agent = true
    artillery.ssh.insert_key = false

    artillery.vm.provider "virtualbox" do |v|
        v.memory = "4096"
    end
  end
end
