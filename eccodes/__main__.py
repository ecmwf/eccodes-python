#
# Copyright 2017-2019 European Centre for Medium-Range Weather Forecasts (ECMWF).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Authors:
#   Alessandro Amici - B-Open - https://bopen.eu
#

import argparse

from . import codes_get_api_version


def selfcheck():
    print("Found: ecCodes v%s." % codes_get_api_version())
    print("Your system is ready.")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('command')
    args = parser.parse_args(args=argv)
    if args.command == 'selfcheck':
        selfcheck()
    else:
        raise RuntimeError("Command not recognised %r. See usage with --help." % args.command)


if __name__ == '__main__':  # pragma: no cover
    main()
