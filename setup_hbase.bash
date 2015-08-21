#!/bin/bash

set -xueo pipefail

sudo apt-get update
sudo apt-get -y dist-upgrade

# # not super necessary, but makes work within the VM more pleasant
sudo apt-get -y install git zsh htop curl

sudo mkdir -p -m777 /mnt/external/clones
sudo chsh -s /bin/zsh vagrant

sudo apt-get -y install python-pip python-virtualenv python-software-properties python-dev debconf-utils

sudo add-apt-repository -y 'ppa:webupd8team/java'
sudo apt-get update

echo oracle-java7-installer shared/accepted-oracle-license-v1-1 select true | sudo /usr/bin/debconf-set-selections

sudo apt-get -y install oracle-java7-installer oracle-java7-set-default

sudo mkdir -p -m0755 /data
sudo chown vagrant:vagrant /data

cat > /home/vagrant/.ssh/config <<EOF
Host localhost
  StrictHostKeyChecking no
Host 0.0.0.0
  StrictHostKeyChecking no
EOF

if [[ ! -f /home/vagrant/.ssh/id_rsa ]]; then
    ssh-keygen -t rsa -N '' -C "for hadoop" -f /home/vagrant/.ssh/id_rsa
fi

cat /home/vagrant/.ssh/id_rsa.pub >> /home/vagrant/.ssh/authorized_keys

cd
if [[ -f /vagrant/Dropbox\ \(Personal\)/binaries/hadoop-2.7.1.tar.gz ]]; then
    cp /vagrant/Dropbox\ \(Personal\)/binaries/hadoop-2.7.1.tar.gz .
elif [[ ! -f hadoop-2.7.1.tar.gz ]]; then
    wget http://apache.osuosl.org/hadoop/common/hadoop-2.7.1/hadoop-2.7.1.tar.gz
fi

sudo mkdir -p -m0755 /data/hadoop
sudo chown -R vagrant:vagrant /data/hadoop
gunzip hadoop-2.7.1.tar.gz --decompress --stdout | tar -mxpf - --strip-components=1 -C /data/hadoop/

echo "export HADOOP_PREFIX=/data/hadoop" >> ~/.profile

echo "export JAVA_HOME=/usr/lib/jvm/java-7-oracle/jre" >> /data/hadoop/etc/hadoop/hadoop-env.sh

cat > /data/hadoop/etc/hadoop/core-site.xml <<EOF
<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>hadoop.tmp.dir</name>
        <value>/data/hadoop</value>
    </property>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:54310</value>
    </property>
</configuration>
EOF

cat > /data/hadoop/etc/hadoop/hdfs-site.xml <<EOF
<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>1</value>
    </property>
</configuration>
EOF

cd /data/hadoop

if [[ ! -d /data/hadoop/dfs/name ]]; then
    ./bin/hdfs namenode -format
fi

cd
if [[ -f /vagrant/Dropbox\ \(Personal\)/binaries/hbase-1.1.1-bin.tar.gz ]]; then
    cp /vagrant/Dropbox\ \(Personal\)/binaries/hbase-1.1.1-bin.tar.gz .
elif [[ ! -f hbase-1.1.1-bin.tar.gz ]]; then
    wget http://mirror.nexcess.net/apache/hbase/1.1.1/hbase-1.1.1-bin.tar.gz
fi

sudo mkdir -p -m0755 /data/{hbase,zk}
sudo chown -R vagrant:vagrant /data/{hbase,zk}

gunzip hbase-1.1.1-bin.tar.gz --decompress --stdout | tar -mxpf - --strip-components=1 -C /data/hbase/

cat > /data/hbase/conf/hbase-site.xml <<EOF
<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>hbase.rootdir</name>
        <value>hdfs://localhost:54310/hbase</value>
    </property>
    <property>
        <name>hbase.cluster.distributed</name>
        <value>true</value>
    </property>
    <property>
        <name>hbase.zookeeper.quorum</name>
        <value>localhost</value>
    </property>
    <property>
        <name>hbase.zookeeper.property.dataDir</name>
        <value>/data/zk/</value>
    </property>
</configuration>
EOF

echo "export JAVA_HOME=/usr/lib/jvm/java-7-oracle/jre" >> /data/hbase/conf/hbase-env.sh
echo "export HBASE_MANAGES_ZK=false" >> /data/hbase/conf/hbase-env.sh
echo "export PATH=$PATH:/data/hbase/bin/:" >> ~/.bashrc
echo 'export PS1="[\u@\h \W]\\$ "' | ed ~/.bashrc
source ~/.bashrc

if ! pgrep -f proc_datanode; then
    /data/hadoop/sbin/start-dfs.sh
fi

if ! pgrep -f proc_zookeeper; then
    /data/hbase/bin/hbase-daemon.sh start zookeeper
fi

if ! pgrep -f proc_regionserver; then
    /data/hbase/bin/start-hbase.sh
fi

if ! pgrep -f proc_thrift; then
    /data/hbase/bin/hbase-daemon.sh start thrift
fi
