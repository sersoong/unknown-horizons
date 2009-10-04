# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################
import random
import tempfile
import sys
import shutil
import re
import string

from horizons.util import Circle, Rect, Point, DbReader
from horizons.constants import GROUND, PATHS

# this is how a random island id looks like (used for creation)
_random_island_id_template = "random:${creation_method}:${width}:${height}:${seed}"

# you can check for a random island id with this:
_random_island_id_regexp = r"random:([0-9]+):([0-9]+):([0-9]+):([\-]?[0-9]+)"


def is_random_island_id_string(id_string):
	"""Returns wheter id_string is an instance of a random island id string"""
	return bool(re.match(_random_island_id_regexp, id_string))

def create_random_island(id_string):
	"""Creates a random island as sqlite db.
	It is rather primitive; it places shapes on the dict.
	@param id_string: random island id string
	@return: sqlite db reader containing island
	"""
	match_obj = re.match(_random_island_id_regexp, id_string)
	assert match_obj
	creation_method, width, height, seed = [ long(i) for i in match_obj.groups() ]

	assert creation_method == 0, "Only one random island creation method is supported for now"

	map_db = DbReader(":memory:")
	map_db("CREATE TABLE ground(x INTEGER NOT NULL, y INTEGER NOT NULL, ground_id INTEGER NOT NULL)")
	map_db("CREATE TABLE island_properties(name TEXT PRIMARY KEY NOT NULL, value TEXT NOT NULL)")
	map_db("BEGIN TRANSACTION")

	rand = random.Random(seed)

	# place this number of tiles
	for i in xrange( int(float(width+height)/2 * 1.5) ):
		x = rand.randint(4, width-4)
		y = rand.randint(4, height -4)

		# place shape determined by shape_id on (x, y)
		shape_id = rand.randint(1, 4)

		if shape_id == 1:
			# use a rect
			for shape_coord in Rect.init_from_topleft_and_size(x-2, y-2, 4, 4).tuple_iter():
				map_db("INSERT INTO ground VALUES(?, ?, ?)", shape_coord[0], shape_coord[1], \
				       GROUND.DEFAULT_LAND)
		else:
			# use a circle, where radius is determined by shape_id
			for shape_coord in Circle(Point(x, y), shape_id).tuple_iter():
				map_db("INSERT INTO ground VALUES(?, ?, ?)", shape_coord[0], shape_coord[1], \
				       GROUND.DEFAULT_LAND)
	map_db("COMMIT")
	return map_db


def generate_map(seed = None):
	"""Generates a whole map.
	@param seed: argument passed to random.seed
	@return filename to the sqlite db containing the new map"""
	rand = random.Random(seed)

	filename = tempfile.mkstemp()[1]
	shutil.copyfile(PATHS.SAVEGAME_TEMPLATE, filename)

	db = DbReader(filename)

	island_space = (35, 35)
	island_min_size = (25, 25)
	island_max_size = (30, 30)

	# generate up to 9 islands
	for i in Rect.init_from_topleft_and_size(0, 0, 3, 3):
		if rand.randint(0, 2) != 0: # 2/3 chance for an island here
			x = i.x * island_space[0]
			y = i.y * island_space[1]
			island_seed = rand.randint(-sys.maxint, sys.maxint)
			island_params = {'creation_method': 0, 'seed': island_seed, \
			                 'width': rand.randint(island_min_size[0], island_max_size[0]), \
			                 'height': rand.randint(island_min_size[1], island_max_size[1])}

			island_string = string.Template(_random_island_id_template).safe_substitute(island_params)

			db("INSERT INTO island (x, y, file) VALUES(?, ?, ?)", x, y, island_string)


	return filename

