import boto3
import click

session = boto3.Session(profile_name='shotty')
ec2 = session.resource('ec2')


def filter_instances(project):
    instances = []

    if project:
        filters=[{'Name':'tag:Project', 'Values':[project]}]
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances = ec2.instances.all()
    return instances

@click.group()
def cli():
    """Shotty manage EC2 snapshots"""

@cli.group('instances')
def instances():
        """Command for instances"""

@instances.command('list')
@click.option('--project', default=None,
    help="Only instances in project (tag Project:<name>)")

def list_instances(project):

    instances = filter_instances(project)

    for i in instances:
        tags = {t['Key']:t['Value'] for t in i.tags or []}
        print(", ".join((
            i.id,
            i.state['Name'],
            i.placement['AvailabilityZone'],
            i.instance_type,
            i.public_dns_name,
            tags.get('Project', 'no project')))
        )
    return



if __name__ == '__main__':
    cli()
