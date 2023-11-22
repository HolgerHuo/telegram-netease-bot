import yaml
import logging
import sys, os

logger = logging.getLogger(__name__)

# Load and test config.yml
try:
    config = yaml.safe_load(open('config.yml'))
    log_level = config['general']['loglevel']
    token = config['general']['token']
    threads = config['general']['threads']
    tmp_dir = os.path.join(os.path.abspath(config['general']['tmpdir']),'')
    ncmapi = config['netease']['neteaseapi']
    ncmuserid = config['netease']['userid']
except Exception as e:
    logger.critical("config.yml is not valid!")
    logger.debug(e)
    sys.exit()

# Check if temporary directory is writable
try:
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    os.access(tmp_dir, os.W_OK)
except Exception as e:
    logger.critical("Temp directory not writable!!!")
    logger.debug(e)
    sys.exit()