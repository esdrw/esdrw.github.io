import copy
import mistune
import os
import pystache
import re
import shutil
import sys
import yaml
from pathlib import Path

ROOT_DIR = 'site-src'
GEN_DIR = 'generator'
BUILD_DIR = 'tmp-site-build'
FINAL_DIR = 'site-build'

# Constants used for rendering
ASSETS_DIR = os.path.join(GEN_DIR, 'assets')
TEMPLATES_DIR = os.path.join(GEN_DIR, 'templates')

GLOBAL_VARS_FILE = os.path.join(ROOT_DIR, 'global.yml')
BASIC_VARS = { 'url-home': '/', 'url-about': '/about/' }

MISTUNE = mistune.Markdown()

debug = False

def build_and_check_path(*arg):
    path = os.path.join(*arg)
    if not Path(path).exists():
        print("Could not find file or directory at \"%s\"." % path)
        exit(1)
    return path

def templates_common_path(*arg):
    return os.path.join(GEN_DIR, 'templates', 'common', *arg)

def templates_posts_path(*arg):
    return os.path.join(GEN_DIR, 'templates', 'posts', *arg)

def templates_about_path(*arg):
    return os.path.join(GEN_DIR, 'templates', 'about', *arg)

def site_build_posts_path(*arg):
    return os.path.join(BUILD_DIR, 'posts', *arg)

def site_build_about_path(*arg):
    return os.path.join(BUILD_DIR, 'about', *arg)

def site_src_posts_path(*arg):
    return build_and_check_path(ROOT_DIR, 'posts', *arg)

def site_src_about_path(*arg):
    return build_and_check_path(ROOT_DIR, 'about', *arg)

def update_with_file_vars(vars_dict, fname):
    new_vars = {}
    with open(fname) as f:
        new_vars = yaml.safe_load(f)

    vars_dict.update(new_vars)

def update_with_vars_from_file(vars_dict, dir_with_vars_file):
    src_files = os.listdir(dir_with_vars_file)

    # There should be at most one .yml file with post variables
    vars_file = first_match(re.compile('.*yml'), src_files)
    if vars_file != None:
        update_with_file_vars(vars_dict, os.path.join(dir_with_vars_file, vars_file))
    return vars_dict

def parse_global_vars(basic_vars):
    update_with_file_vars(basic_vars, GLOBAL_VARS_FILE)
    return basic_vars

def first_match(regex, li):
    matches = list(filter(lambda s: re.search(regex, s) != None, li))
    if len(matches) == 0:
        return None
    return matches[0]

# Move the assets into the top level of the build dir.
# Also create the build dir.
def move_assets():
    try:
        if os.path.exists(ASSETS_DIR):
            shutil.copytree(ASSETS_DIR, os.path.join(BUILD_DIR, 'assets'))
        else:
            os.mkdir(BUILD_DIR)
    except FileExistsError:
        print("Build directory %s already exists. Please remove and try again." % BUILD_DIR)
        exit(1)

def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def render_markdown_from_file(content_dir):
    src_files = os.listdir(content_dir)

    # There should be exactly one .md file with post content
    content_file = first_match(re.compile('.*md'), src_files)

    if content_file == None:
        print("Content not found for post \"%s\". Please create the file and try again." % content_dir)
        exit(1)
    return MISTUNE(read_file(os.path.join(content_dir, content_file)))

def render_common(templ_vars):
    common_vars = {}
    for fname in os.listdir(templates_common_path()):
        templ = read_file(templates_common_path(fname))
        # Use the first word parsed out of the filename for referencing the rendered
        # template in the future.
        var_name = fname.split('.')[0]
        common_vars[var_name] = pystache.render(templ, templ_vars)
    templ_vars['common'] = common_vars
    return templ_vars

# post_templ: content of post template
# templ_vars: template variables from common or global
# post_dir: the directory name of the current post being rendered
def render_post(post_templ, templ_vars, post_dir):
    new_vars = copy.deepcopy(templ_vars)
    post_vars = {}
    update_with_vars_from_file(post_vars, site_src_posts_path(post_dir))
    post_vars['content'] = render_markdown_from_file(site_src_posts_path(post_dir))

    os.makedirs(site_build_posts_path(post_dir))
    new_vars['post'] = post_vars
    if debug:
        print("Resolved post variables...")
        print(list(post_vars.keys()))
    with open(site_build_posts_path(post_dir, 'index.html'), 'w') as f:
        f.write(pystache.render(post_templ, new_vars))

def render_posts(templ_vars):
    post_templ_files = os.listdir(templates_posts_path())
    post_templ = read_file(templates_posts_path('index.html.mustache'))

    print(site_src_posts_path())
    for dname in os.listdir(site_src_posts_path()):
        if debug:
            print("Rendering post...")
            print(dname)
        render_post(post_templ, templ_vars, dname)

def render_about(templ_vars):
    new_vars = copy.deepcopy(templ_vars)
    templ = read_file(templates_about_path('index.html.mustache'))

    about_vars = {}
    update_with_vars_from_file(about_vars, site_src_about_path())
    about_vars['content'] = render_markdown_from_file(site_src_about_path())

    os.makedirs(site_build_about_path())
    new_vars['about'] = about_vars
    if debug:
        print("Resolved about variables...")
        print(list(about_vars.keys()))
    with open(site_build_about_path('index.html'), 'w') as f:
        f.write(pystache.render(templ, new_vars))

def render_site():
    move_assets()

    templ_vars = parse_global_vars(BASIC_VARS)
    if debug:
        print("Parsed global vars...")
        print(templ_vars)

    # Render common templates
    templ_vars = render_common(templ_vars)
    if debug:
        print("Rendered common templates...")
        print(templ_vars.keys())

    # Render posts
    render_posts(templ_vars)

    # Render about page
    render_about(templ_vars)

    # Render the homepage
    # render_home(templ_vars)

    # Move build dir into final dir

# This script must be run from the directory above generator/
def main():
    global debug
    if len(sys.argv) > 1 and sys.argv[1] == '-d':
        debug = True
    render_site()

if __name__ == '__main__':
    main()
