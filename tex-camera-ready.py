#!/usr/local/bin/python3
import argparse
import collections
import os
import re
import shutil
import sys
from PIL import Image


def refactor_dependencies(old_file, new_file, root_dir):
    regexps = [" (table|graphics) {0,1}(\[[^\]]*\]){0,1} {0,}\{([^\}]*)\}",
               "(includegraphics|input|include)(\[[^\]]*\]){0,}\{([^\}]*)\}"]
    missing_files = []
    included = []
    new_commands = {}
    standalone_mode = False
    root_dir = os.path.join(root_dir, 'resources')
    print('   Refactoring file {} -> {}'.format(old_file, new_file))

    with open(new_file, 'w') as of:
        with open(old_file) as f:
            lines = f.readlines()

        for line in lines:

            if line.strip().startswith('%'): continue

            # Check if this is a standalone class - requires different file handling
            if re.search("documentclass(\[[^\]]*\]){0,1}\{standalone\}", line):
                standalone_mode = True

            # Check for simple new commands - used for referencing external resources
            new_command = re.search("newcommand\*{0,1}\{([^\}]*)\}\{([^\}]*)\}", line)

            # Build dictionary of new commands
            if new_command:
                key, value = new_command.groups()
                if key in ['\\DataPath', '\\FigPath']:
                    new_commands[key] = value
                    line = '\\newcommand*{{{}}}{{{}}}\n'.format(key, '../resources/')

            # Handle inclusion of graphics / data files

            # Check for known inclusion commands
            for pattern in regexps:
                match = re.search(pattern, line)
                if match:
                    command, params, filename = match.groups()
                    if standalone_mode:
                        for k, v in new_commands.items():
                            filename = re.sub(re.escape(k) + '( |\{\})', v, filename)

                    # Make sure the file exists & rewrite the line
                    full_path = '{}/{}'.format(os.path.split(old_file)[0], filename) if old_file.find(
                        '/') >= 0 else filename

                    if os.path.isfile(full_path):
                        if filename not in included:
                            print('   {:15}  {}'.format('               ', filename))
                    else:
                        if filename not in included:
                            print('   {:15}! {}'.format('               ', filename))
                        missing_files.append(filename)

                    if len(new_commands.keys()) > 0:
                        new_filename = '{} {}/{}'.format(list(new_commands.keys())[0], os.path.split(new_file)[-1].split('.')[0], os.path.split(filename)[-1])
                    else:
                        new_filename = '{}/{}/{}'.format('./resources', os.path.split(new_file)[-1].split('.')[0], os.path.split(filename)[-1])

                    tgt_filaname = '{}/{}/{}'.format(root_dir, os.path.split(new_file)[-1].split('.')[0], os.path.split(filename)[-1])
                    if not os.path.isdir(os.path.split(tgt_filaname)[0]):
                        os.makedirs(os.path.split(tgt_filaname)[0])
                    if os.path.isfile(full_path):
                        shutil.copyfile(full_path, tgt_filaname)

                    # Update the command with a new filename in the current line
                    # (re module parses backslashes, so make sure to prevent that)
                    line = re.sub(pattern, '{}{}{{{}}}'.format(command, params, new_filename).replace('\\', '\\\\'), line)

                    included.append(filename)

            of.write(line)

    return missing_files


parser = argparse.ArgumentParser(
    description='LaTeX source cleanup: take a working LaTeX sources and export a copy for dissemination (with '
                'resource refactoring, bibtex items selection, etc.)')
parser.add_argument('filename', type=str, help='input file (*.tex)')
parser.add_argument('-o', '--output', type=str, help='Output directory, default: ./final')
parser.add_argument('-c', '--crop', help='Crop bitmaps based on LaTeX trim parameters', action='store_true')
parser.add_argument('-v', '--verbose', help='Print analysis summary to stdout', action='store_true')
parser.add_argument('-f', '--force', help='Force output to an existing directory', action='store_true')
parser.add_argument('-b', '--bib', help='Cleanup Bibtex entries (leave only cited)', action='store_true')
args = parser.parse_args()

supported_formats = ['.tex']

# Verify params
if not os.path.splitext(args.filename)[-1].lower() in supported_formats:
    print('Error: Unsupported document format ({})'.format(os.path.split(args.filename)[-1]))
    sys.exit(1)

if not args.output:
    args.output = './final_new'

if os.path.isdir(args.output) and not args.force:
    print('Error: directory {} exists!'.format(args.output))
    sys.exit(2)

current_environment = collections.deque()

resources = []
counters = {'figure': 0, 'table': 0, 'algorithm': 0}

input_root = os.path.dirname(args.filename)
input_root = input_root if len(input_root) > 0 else '.'

# Read lines from the input file
with open(args.filename) as f:
    lines = f.readlines()

missing_deps = {}

print('Loaded {} lines from {}'.format(len(lines), args.filename))
print('Writing to {}'.format(args.output))

for dirname in [args.output, '{}/bib'.format(args.output), '{}/resources'.format(args.output), '{}/includes'.format(args.output)]:
    if not os.path.exists(dirname): os.mkdir(dirname)

# Open target file
of = open(os.path.join(args.output, os.path.split(args.filename)[-1]), 'w')

subfig_count = 0
current_subfig = 0
alphabet = 'abcdefghijklmnopqrstuwvxyz'
citations = []
bibtex_files = []

# Process successive lines 
for line in lines:

    if line.strip().startswith('%'):
        continue

    line_written = False
    env_command = re.search('(begin|end){([a-z]*)\*{0,1}\}', line)

    if env_command:
        flag, env_type = env_command.groups()
        if flag == 'begin':
            current_environment.append(env_type)
            if current_environment[-1] in counters:
                counters[current_environment[-1]] += 1
                current_subfig = 0
        elif flag == 'end':
            current_environment.pop()
        else:
            print('Parsing error in line: {}'.format(line))
            sys.exit(3)

    new_command = re.search("newcommand\*{0,1}\{([^\}]*)\}\{([^\}]*)\}", line)

    # Replace simple new commands that control external resources
    if new_command:
        key, value = new_command.groups()
        if key in ['\\DataPath', '\\FigPath']:
            line = '\\newcommand*{{{}}}{{{}}}\n'.format(key, './resources/')

    include_command = re.search("(includegraphics|input|include|includestandalone)(\[[^\]]*\]){0,1}\{([^\}]*)\}", line)

    if include_command:
        command, params, filename = include_command.groups()

        if command in ['input', 'include', 'includestandalone']:
            # If filename not explicit, fallback to *.tex
            if not os.path.isfile(filename) and not filename.endswith('.tex'):
                filename = '{}.tex'.format(filename)
            if not os.path.isfile(filename):
                print('Error {} not found in the filesystem'.format(filename))
                sys.exit(5)

        # The sub-extension handles multiple includes in a single figure (
        subext = '' if current_subfig <= 0 else alphabet[current_subfig]
        extension = "" if len(filename.split('.')) == 1 else ".%s" % filename.split('.')[-1]

        filename_split = os.path.split(filename)
        context = '{} {:02}{}'.format(current_environment[-1], counters[current_environment[-1]], subext) if current_environment[-1] in counters else 'document'
        context_file = '{}_{:02}{}{}'.format(current_environment[-1], counters[current_environment[-1]], subext, extension) if current_environment[-1] in counters else filename_split[-1]

        new_filename = 'includes/{}'.format(context_file)
        current_subfig += 1

        print('\n + {:15}: {}'.format(context, filename))
        print('   {:15}> {}'.format('               ', new_filename))


        if filename.endswith('.tex'):
            # If the referenced file is a TikZ or PGF figure, refactor its dependencies
            missing_deps[filename] = refactor_dependencies(filename, '{}/{}'.format(args.output, new_filename), args.output)
        else:
            # Look for cropping in parameters
            cropopt = re.search('trim=([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)', params) if args.crop else None

            # If the file is a graphics file, and cropping was requested, trim the bitmap and save...
            if args.crop and command == "includegraphics" and cropopt:

                l, b, r, t = cropopt.groups()

                # Crop the image
                im = Image.open("%s/%s" % (input_root, filename))
                w, h = im.size
                dpi = im.info["dpi"] if 'dpi' in im.info else 72
                if not isinstance(dpi, tuple):
                    dpi = (dpi, dpi)
                im.crop((int(l) * dpi[0] / 72, int(t) * dpi[1] / 72, w - int(r) * dpi[0] / 72,
                         h - int(b) * dpi[1] / 72)).save('{}/{}'.format(args.output, new_filename))

                # Remove trimming commands from the parameters
                params = re.sub('trim=([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)', '', params)
                params = re.sub('clip', '', params)
                params = re.sub(',,', ',', params)
                params = params.replace("[,", "[")
                params = params.replace(",]", "]")
                print('   {:15}T {}'.format('               ', 'clipped bitmap'))

            else:
                shutil.copyfile(filename, '{}/{}'.format(args.output, new_filename))

        if not params:
            params = ''

        if len(params) > 0:
            params = params.replace('\\', '\\\\')

        if command == 'includestandalone':
            new_filename = new_filename.replace('.tex', '')

        line = re.sub("(includegraphics|input|include|includestandalone)(\[[^\]]*\]){0,1}\{([^\}]*)\}", "%s%s{%s}" % (command, params, new_filename), line)

    if args.bib:

        # Find citations
        for r in re.findall('\\\\cite\{([\w0-9:\-\_\,\.]+)\}', line):
            for i in r.split(','):
                citations.append(i)

        # Find included BibTeX databases
        bib_result = re.findall('bibliography\{([^\]]+)\}', line)
        if bib_result:
            of.write(re.sub('(bibliography)\{([^\]]+)\}', '\\1{bib/references.bib}', line))
            line_written = True
            for r in bib_result:
                for i in r.split(','):
                    bibtex_files.append(i)

    if not line_written:
        of.write(line)

of.close()

if sum([len(v) for v in missing_deps.values()]) > 0:
    print('\nMissing dependencies (you may need to handle them manually):')
    for k, v in missing_deps.items():
        if len(v) > 0:
            print(' + {}'.format(k))
            for name in v:
                print('   {}'.format(name))

                # Process collected bibliography information
if args.bib:

    found_citations = sorted(set(citations))
    print('\nFound {} citations:'.format(len(found_citations)))
    index = 1
    for ref in found_citations:
        print('  [{}] {}'.format(index, ref))
        index += 1
    print('Found {} Bibtex databases: {}'.format(len(bibtex_files), bibtex_files))

    matched_citations = {}

    for bib_file in bibtex_files:

        print('Parsing {}'.format(bib_file))

        if not bib_file.endswith(".bib") and not os.path.exists("%s/%s" % (input_root, bib_file)):
            bib_file = "%s.bib" % bib_file

        with open("%s/%s" % (input_root, bib_file)) as bf:
            content = bf.read()
            # TODO Could use a better regexp for pinpointing BibTeX entries - the current one needs the closing bracket in a separate line.
            matches = re.findall('(@[\w0-9:\-\_\,\.]+\{(.(?!\n\}))+..\})', content, re.DOTALL)  # [^\}]*(?=\n\})

            # iterate over found entries
            for entry in matches:
                entry_text = entry[0]
                # Add to dictionary
                name = re.findall('^@[\w]+\{([^,]+),', entry_text)
                if len(name) > 0 and name[0] in found_citations:
                    matched_citations[name[0]] = entry_text

                # Sanity check - make sure only one entry has been matched (due to the limitation stated above)
                count_tags = re.findall('\s(t|T)itle', entry_text)
                if len(count_tags) != 1 and len(name) > 0:
                    print('Warning Suspicious bibtext entry for {} : {} title entries!'.format(name[0], len(count_tags)))

    print('Matched {} entries'.format(len(matched_citations)))

    if len([v for v in found_citations if v not in matched_citations.keys()]) > 0:
        print('Missing ones: {}'.format([v for v in found_citations if v not in matched_citations.keys()]))

    with open("%s/bib/references.bib" % (args.output), 'w') as of:
        for name in sorted(matched_citations.keys()):
            of.write("%s\n\n" % matched_citations[name])
