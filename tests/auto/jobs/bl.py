# Imports
import datetime


def run(job_obj):
    pass


def remove_pr_data(job_obj):
    logger = job_obj.logging.getLogger('JOB/REMOVE_PR_DATA')
    rm_command = [
                 [f'rm -rf {job_obj.rt_dir}', job_obj.pr_repo_loc],
                 [f'rm -rf {job_obj.repo_dir_str}', job_obj.pr_repo_loc]
                 ]
    job_obj.run_commands(logger, rm_command)


def clone_pr_repo(job_obj):
    ''' clone the GitHub pull request repo, via command line '''
    logger = job_obj.logging.getLogger('JOB/CLONE_PR_REPO')
    repo_name = job_obj.preq_dict['preq'].head.repo.name
    job_obj.branch = job_obj.preq_dict['preq'].head.ref
    git_url = job_obj.preq_dict['preq'].head.repo.html_url.split('//')
    git_url = f'{git_url[0]}//${{ghapitoken}}@{git_url[1]}'
    logger.debug(f'GIT URL: {git_url}')
    logger.info('Starting repo clone')
    job_obj.repo_dir_str = f'{job_obj.machine["workdir"]}/\
                        {str(job_obj.preq_dict["preq"].id)}/\
                        {datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
    job_obj.pr_repo_loc = job_obj.repo_dir_str+"/"+repo_name
    job_obj.comment_text_append(f'Repo location: {job_obj.pr_repo_loc}')
    create_repo_commands = [
        [f'mkdir -p "{job_obj.repo_dir_str}"', job_obj.machine['workdir']],
        [f'git clone -b {job_obj.branch} {git_url}', job_obj.repo_dir_str],
        ['git submodule update --init --recursive',
         f'{job_obj.repo_dir_str}/{repo_name}'],
        ['git config user.email "brian.curtis@noaa.gov"',
         f'{job_obj.repo_dir_str}/{repo_name}'],
        ['git config user.name "Brian Curtis"',
         f'{job_obj.repo_dir_str}/{repo_name}']
    ]

    job_obj.run_commands(logger, create_repo_commands)

    logger.info('Finished repo clone')
    return job_obj.pr_repo_loc
