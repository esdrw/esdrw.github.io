import copy
import os
import pystache
import re
import shutil
import sys
import yaml

ROOT_DIR = 'site-src'
GEN_DIR = 'generator'
BUILD_DIR = 'tmp-site-build'
FINAL_DIR = 'site-build'

# Constants used for rendering
ASSETS_DIR = os.path.join(GEN_DIR, 'assets')
TEMPLATES_DIR = os.path.join(GEN_DIR, 'templates')

GLOBAL_VARS_FILE = os.path.join(ROOT_DIR, 'global.yml')
BASIC_VARS = { 'url-home': '/', 'url-about': '/about/' }

debug = False

def templates_common_path(*arg):
    return os.path.join(GEN_DIR, 'templates', 'common', *arg)

def templates_posts_path(*arg):
    return os.path.join(GEN_DIR, 'templates', 'posts', *arg)

def site_build_posts_path(*arg):
    return os.path.join(BUILD_DIR, 'posts', *arg)

def site_src_posts_path(*arg):
    return os.path.join(ROOT_DIR, 'posts', *arg)

def update_with_file_vars(vars_dict, fname):
    new_vars = {}
    with open(fname) as f:
        new_vars = yaml.safe_load(f)

    vars_dict.update(new_vars)

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
        print("Build directory " + BUILD_DIR + " already exists. Please remove and try again.")
        exit(1)

def render_common(templ_vars):
    common_vars = {}
    for fname in os.listdir(templates_common_path()):
        f = open(templates_common_path(fname), 'r')

        # Use the first word parsed out of the filename for referencing the rendered
        # template in the future.
        var_name = fname.split('.')[0]
        common_vars[var_name] = pystache.render(f.read(), templ_vars)
    templ_vars['common'] = common_vars
    print(templ_vars)
    return templ_vars

# post_templs: dictionary mapping from a template name (sans mustache extension) to the template content
# templ_vars: template variables from common or global
# post_dir: the directory name of the current post being rendered
def render_post(post_templs, templ_vars, post_dir):
    new_vars = copy.deepcopy(templ_vars)
    src_files = os.listdir(site_src_posts_path(post_dir))

    # There should be exactly one .yml file with post variables
    vars_file = first_match(re.compile('.*yml'), src_files)

    # There should be exactly one .md file with post content
    content_file = first_match(re.compile('.*md'), src_files)
    post_vars = {}
    if vars_file != None:
        update_with_file_vars(post_vars, site_src_posts_path(post_dir, vars_file))
    if content_file == None:
        print("Content not found for post \"%s\". Please clean up and try again." % post_dir)
        exit(1)

    post_vars['content'] = 'Test' # render_markdown(content_file)
    for templ_name in post_templs:
        new_vars['post'] = post_vars
        os.makedirs(site_build_posts_path(post_dir))
        if debug:
            print("Resolved post variables...")
            print(post_vars)
        with open(site_build_posts_path(post_dir, templ_name), 'w+') as f:
            f.write(pystache.render(post_templs[templ_name], new_vars))

def render_posts(templ_vars):
    dir_name = 'posts'
    post_templ_files = os.listdir(templates_posts_path())
    post_templs = {}
    for templ_file in post_templ_files:
        with open(templates_posts_path(templ_file), 'r') as f:
            # Exclude the ".mustache" extension.
            gen_fname = '.'.join(templ_file.split('.')[:-1])
            post_templs[gen_fname] = f.read()

    if debug:
        print("Rendering each post to have these files...")
        print(list(post_templs.keys()))

    for dname in os.listdir(site_src_posts_path()):
        if debug:
            print("Rendering post...")
            print(dname)
        render_post(post_templs, templ_vars, dname)

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

    # Render posts
    #  render_top()

    # Move build dir into final dir

# This script must be run from the directory above generator/
def main():
    global debug
    if len(sys.argv) > 1 and sys.argv[1] == '-d':
        debug = True
    render_site()

if __name__ == '__main__':
    main()
