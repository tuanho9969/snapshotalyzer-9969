import boto3
import click
import botocore

session = boto3.Session(profile_name='shotty')
ec2 = session.resource('ec2')


def filter_instances(project, instance):
    instances = []

    if project:
        filters=[{'Name':'tag:Project', 'Values':[project]}]
        instances = ec2.instances.filter(Filters=filters)
    elif instance:
        instances = ec2.instances.filter(Filters=[{'Name':'instance-id', 'Values':[instance]}])
    else:
        instances = ec2.instances.all()
    return instances

def has_pending_snapshot(volumes):
    snapshots = list(volumes.snapshots.all())
    return snapshots and snapshots[0].state == "pending"

@click.group()
def cli():
    """Shotty manage EC2 snapshots"""

@cli.group('instances')
def instances():
        """Command for instances"""

@instances.command('list')
@click.option('--project', default=None,
    help="Only instances in project (tag Project:<name>)")
@click.option('--instance', default=None,
    help="Only instance with specific instance ID")

def list_instances(project, instance):

    instances = filter_instances(project, instance)

    for i in instances:
        tags = { t['Key'] : t['Value'] for t in i.tags or []}
        print(", ".join((
            i.id,
            i.state['Name'],
            i.placement['AvailabilityZone'],
            i.instance_type,
            i.public_dns_name,
            tags.get('Project', 'no project')))
        )
    return

@instances.command('start')
@click.option('--project', default=None,
    help="Only instances in project (tag Project:<name>)")
@click.option('--instance', default=None,
    help="Only instance with specific instance ID")

def start_instances(project,instance):
    "Start EC2 instances"

    instances = filter_instances(project,instance)

    for i in instances:
        print("Starting {0}".format(i.id))
        try:
            i.start()
        except botocore.exceptions.ClientError as e:
            print("Could not start {0}".format(i.id) + str(e))
            continue
    return

@instances.command('stop')
@click.option('--project', default=None,
    help="Only instances in project (tag Project:<name>)")
@click.option('--instance', default=None,
    help="Only instance with specific instance ID")

def stop_instances(project,instance):
    "Stop EC2 instances"

    instances = filter_instances(project,instance)

    for i in instances:
        print("Stopping {0}".format(i.id))
        try:
            i.stop()
        except botocore.exceptions.ClientError as e:
            print("Could not stop {0}".format(i.id) + str(e))
            continue
    return

@instances.command('snapshots')
@click.option('--project', default=None,
    help="Only snapshots in project (tag Project:<name>)")
@click.option('--instance', default=None,
    help="Only instance with specific instance ID")

def snapshot_instances(project,instance):
    "Take snapshot for EC2 instances"

    instances = filter_instances(project,instance)
    for i in instances:
        print("Stopping {0}".format(i.id))

        i.stop()
        i.wait_until_stopped()
        for v in i.volumes.all():
            if has_pending_snapshot(v):
                print("Skipping {0}, snapshot already in progress".format(v.id))
                continue
            print("Creating snapshot of {0}".format(v.id))
            try:
                v.create_snapshot(Description="Created by Snapshotalyzer 30000")
            except botocore.exceptions.ClientError as e:
                print("Cannot create snapshot of {0}".format(v.id) + str(e))
                continue

        print("Starting {0}".format(i.id))
        i.start()
        i.wait_until_running()
    print("Job done!")
    return



@cli.group('volumes')
def volumes():
    """Commands for volumes"""

@volumes.command('list')
@click.option('--project', default=None,
    help="Only instances in project (tag Project:<name>)")
def list_volumes(project):

    instances = filter_instances(project)

    for i in instances:
        for v in i.volumes.all():
            print(', '.join((
            v.id,
            i.id,
            v.state,
            str(v.size) + "GiB",
            v.encrypted and "Encrypted" or "Not Encrypted"
            )))

@cli.group('snapshots')
def snapshots():
    """Commands for snapshots"""

@snapshots.command('list')
@click.option('--project', default=None,
    help="Only instances in project (tag Project:<name>")
@click.option('--all', 'list_all', default=False, is_flag=True,
    help="List all snapshots, not just most recent one")
def list_snapshots(project, list_all):

    instances = filter_instances(project)

    for i in instances:
        for v in i.volumes.all():
            for s in v.snapshots.all():
                print(', '.join((
                    s.id,
                    v.id,
                    i.id,
                    s.state,
                    s.start_time.strftime("%c")
                )))

                if s.state == "completed" and not list_all : break
    return


if __name__ == '__main__':
    cli()
