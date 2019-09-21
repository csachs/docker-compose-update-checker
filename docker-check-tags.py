# Copyright 2019 Christian C. Sachs
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import re
import sys
import time
import bisect
import requests

URL_SCHEMA_GET_TAGS = 'https://hub.docker.com/v2/repositories/' \
                      '{specification}/tags/?page=1&page_size={page_size}&name={name}'

API_SLEEP_TIME = 0.5


def get_tags(specification, name=''):

    specification = specification.split(':')[0]
    if '/' not in specification:
        specification = 'library/' + specification

    args = dict(
        specification=specification,
        name=name,
        page_size=100  # more doesnt seem to be possible?
    )

    results = []

    next_url = URL_SCHEMA_GET_TAGS.format(**args)

    while next_url:

        result = requests.get(next_url)

        assert result.status_code == 200

        data = result.json()

        results += data['results']

        next_url = data['next']

        if next_url:
            time.sleep(API_SLEEP_TIME)

    return results


class magicstr(str):
    def __gt__(self, other):
        return str(self) > str(other)

    def __str__(self):
        return self[:]


class magicint(int):

    def __gt__(self, other):
        if isinstance(other, int):
            return int(self) > other
        else:
            return str(self) > str(other)

    def __str__(self):
        return str(int(self))


def numerize(s):
    try:
        return magicint(s)
    except ValueError:
        return magicstr(s)


def version_split(ver):

    result = []
    for split in re.split(r'(\D+)', ver):
        for inner_split in re.split(r'(\w+)', split):
            if inner_split != '':
                result += [numerize(inner_split)]

    return tuple(result)


def version_join(splits):
    return ''.join(map(str, splits))


def is_non_release(s):
    undesired = ['a', 'alpha', 'b', 'beta', 'rc']
    for undesired_ in undesired:
        if undesired_ in s:
            return True

    return False


def begins_with_word(s):
    return re.sub(r'[a-zA-Z]', '', str(s[0])) == ''


def find_newer(what):
    try:
        version = what.split(':')[1]
    except IndexError:
        # fail early if no version was passed
        return []

    modifier = re.sub(r'[^a-z]', '', version)

    tags = get_tags(what, name=modifier)

    tag_dict = {tag['name']: tag for tag in tags}

    version_frag = version_split(version)

    tag_mapping = {version_split(tag): tag for tag in tag_dict.keys()}

    tags_of_interest = list(tag_mapping.keys())

    filter_rc_beta = True
    if filter_rc_beta:
        tags_of_interest = [tag for tag in tags_of_interest if not is_non_release(tag)]

    ensure_same_versioning = True
    if ensure_same_versioning:
        tags_of_interest = [tag for tag in tags_of_interest if len(tag) == len(version_frag)]

    no_named_releases = True
    if no_named_releases:
        tags_of_interest = [tag for tag in tags_of_interest if not begins_with_word(tag)]

    tags_of_interest = list(sorted(tags_of_interest))

    position = bisect.bisect_left(tags_of_interest, version_frag)

    tags_of_interest = tags_of_interest[position:]

    try:
        pos = tags_of_interest.index(version_frag)
        del tags_of_interest[pos]
    except ValueError:
        pass

    tags_of_interest = [tag_mapping[tag] for tag in tags_of_interest]

    return tags_of_interest


def main():
    import yaml

    file_name = sys.argv[1]
    structure = yaml.load(open(file_name), Loader=yaml.SafeLoader)

    service_list = []

    for service_name, service_structure in structure['services'].items():
        try:
            image_name = service_structure['image']
        except KeyError:
            try:
                image_name = service_structure['build']['args']['BASE']
            except KeyError:
                image_name = None
        service_list.append((service_name, image_name,))

    service_name_maxlen = max([len(a) for a, b in service_list])
    image_name_maxlen = max([len(b) for a, b in service_list])

    for service_name, image_name in service_list:
        print(("[%s]" % service_name).ljust(service_name_maxlen+3), end="")

        if image_name is None:
            print("Could not find image name.")
            continue

        print("Current version: %s " % image_name.ljust(image_name_maxlen), end="")

        update_check = find_newer(image_name)

        if update_check:
            print("The following might be newer: %r" % update_check)
        else:
            print("No newer version found.")


def old_main():
    what = sys.argv[1]
    find_newer(what)


if __name__ == '__main__':
    main()
