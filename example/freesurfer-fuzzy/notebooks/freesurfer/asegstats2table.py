#!/usr/bin/env python

import warnings

warnings.filterwarnings("ignore", ".*negative int.*")

import os
import sys
import optparse
import logging
import csv

import freesurfer.legacy as fsutils
from freesurfer.legacy import AsegStatsParser, BadFileError, aseglogger

# Original Version - Douglas Greve, MGH
# Rewrite - Krish Subramaniam, MGH

# globals
l = aseglogger

# map of delimeter choices and string literals
delimiter2char = {"comma": ",", "tab": "\t", "space": " ", "semicolon": ";"}

HELPTEXT = """
Converts a subcortical stats file created by recon-all and/or
mri_segstats (eg, aseg.stats) into a table in which each line is a
subject and each column is a segmentation ( there is an option to transpose that). 
The values are the volume of the segmentation in mm3 or the mean intensity over the structure.
The first row is a list of the segmentation names. The first column
is the subject name. If the measure is volume, then the estimated
intracranial volume (eTIV) is printed as the 2nd to last column 
(if present in the input), and BrainSegVol is the last column.

The subjects list can be specified in one of four ways:
  1. Specify each subject after -s 
  
          -s subject1 -s subject2 ..
  
  2. specify all subjects after --subjects.  
     --subjects does not have
     to be the last argument. Eg:
     
          --subjects subject1 subject2 ... 

  3. Specify each input file after -i 

          -i subject1/stats/aseg.stats -i subject2/stat/aseg.stats ..
  
  4. Specify all the input stat files after --inputs. --inputs does not have
     to be the last argument. Eg:
       
          --inputs subject1/stats/aseg.stats subject2/stats/aseg.stats ...

The first two methods assume the freesurfer directory structure. The
last two are general and can be used with any file produced by
mri_segstats regardless of whether it was created with recon-all or not,
however, the subject name is not printed in the file (just the row
number). Note that the first two and last two are mutually exclusive. i.e
don't specify --subjects when you are providing --inputs and vice versa.

By default, the volume (mm3) of each segmentation is reported. This
can be changed with '--meas measure', where measure can be 
volume or mean. If mean, it reports the mean intensity value from
the 6th column.

By default, all segmentations found in the input stats file are
reported. This can be changed by specifying the maximum segmentation
number with --maxsegno. This can be convenient for removing
segmentations that are always empty.

With methods 1 and 2 above uses stats/aseg.stats by default. 
This can be changed to subdir/statsfile with --subdir subdir
--statsfile statsfile.

The --common-segs flag outputs only the segmentations which are common to *all*
the statsfiles. This option is helpful if one or more statsfile contains
segmentations different from the segs of other files ( which results in the
script exiting which is the default behavior ). This option makes the
script to continue.

The --all-segs flag outputs segmentations which are the union of all
segmentations in all statsfiles. This option is helpful if one or more statsfile
contains segs different from the segs of other files ( which results in the
script exiting, the default behavior ). Subjects which don't have a certain
segmentation show a value of 0.

The --segids-from-file <file> option outputs only the segmentations present in the file.
There has to be one segmentation id per line in the file. The output table will maintain the 
order of the segmentation ids

The --segno option outputs only the segmentation id requested.
This is useful because if the number of segmentations is large,
the table becomes huge.
The order of the specified seg ids is maintained. 

The --no-segno options doesn't output the segmentations. 
This can be convenient for removing segs that are always empty.

The --transpose flag writes the transpose of the table. 
This might be a useful way to see the table when the number of subjects is
relatively less than the number of segmentations.

The --delimiter option controls what character comes between the measures
in the table. Valid options are 'tab' ( default), 'space', 'comma' and  'semicolon'.

The --skip option skips if it can't find a .stats file. Default behavior is
exit the program.
"""


def options_parse(args=None):
    """
    Command Line Options Parser for asegstats2table
    initiate the option parser and return the parsed object
    """
    parser = optparse.OptionParser(usage=HELPTEXT)

    # help text
    h_sub = "(REQUIRED) subject1 <subject2 subject3..>"
    h_s = " subjectname"
    h_subf = "name of the file which has the list of subjects ( one subject per line)"
    h_qdec = "name of the qdec table which has the column of subjects ids (fsid)"
    h_qdeclong = "name of the longitudinal qdec table which has the column of tp ids (fsid) and subject templates (fsid-base)"
    h_fsgd = "name of the fsgd file to extract subjects from"
    h_inp = " input1 <input2 input3..>"
    h_i = " inputname"
    h_meas = "measure: default is volume ( alt: mean, std)"
    h_max = " maximum segmentation number to report"
    h_segsfile = "filename : output seg ids specified in the file"
    h_seg = "segno1 <segno2 segno3..> : only include given segmentation numbers"
    h_noseg = "segno1 <segno2 segno3..> : exclude given segmentation numbers"
    h_common = "output only the common segmentations of all the statsfiles given"
    h_all = "output all the segmentations of the statsfiles given"
    h_stats = 'use `fname` instead of "aseg.stats"'
    h_subdir = 'use `subdir` instead of "stats/"'
    h_tr = (
        "transpose the table ( default is subjects in rows and segmentations in cols)"
    )
    h_etiv = "report volume as percent estimated total intracranial volume"
    h_t = "(REQUIRED) the output tablefile"
    h_deli = "delimiter between measures in the table. default is tab (alt comma, space, semicolon )"
    h_skip = "if a subject does not have stats file, skip it"
    h_v = "increase verbosity"
    h_vol_extras = "Do not include global volume measures like BrainSegVol"
    h_scale = "scale factor for all values written to outputfile, default value=1"

    # Add options
    parser.add_option(
        "--subjects",
        dest="subjects",
        action="callback",
        callback=fsutils.callback_var,
        help=h_sub,
    )
    parser.add_option("-s", dest="subjects", action="append", help=h_s)
    parser.add_option("--subjectsfile", dest="subjectsfile", help=h_subf)
    parser.add_option("--qdec", dest="qdec", help=h_qdec)
    parser.add_option("--qdec-long", dest="qdeclong", help=h_qdeclong)
    parser.add_option("--fsgd", dest="fsgd", help=h_fsgd)
    parser.add_option(
        "--inputs",
        dest="inputs",
        action="callback",
        callback=fsutils.callback_var,
        help=h_inp,
    )
    parser.add_option("-i", dest="inputs", action="append", help=h_i)
    parser.add_option("-t", "--tablefile", dest="outputfile", help=h_t)
    parser.add_option("--sd", dest="SUBJECTS_DIR")
    parser.add_option(
        "-m",
        "--meas",
        dest="meas",
        choices=(
            "volume",
            "Area_mm2",
            "nvoxels",
            "nvertices",
            "mean",
            "std",
            "snr",
            "max",
        ),
        default="volume",
        help=h_meas,
    )
    parser.add_option("--maxsegno", dest="maxsegno", help=h_inp)
    parser.add_option("--segids-from-file", dest="segidsfile", help=h_segsfile)

    parser.add_option(
        "--segno",
        dest="segnos",
        action="callback",
        callback=fsutils.callback_var,
        help=h_seg,
    )
    parser.add_option(
        "--no-segno",
        dest="no_segnos",
        action="callback",
        callback=fsutils.callback_var,
        help=h_noseg,
    )
    parser.add_option(
        "--common-segs",
        dest="common_flag",
        action="store_true",
        default=False,
        help=h_common,
    )
    parser.add_option(
        "--all-segs", dest="all_flag", action="store_true", default=False, help=h_all
    )
    parser.add_option(
        "--no-vol-extras",
        dest="vol_extras",
        action="store_false",
        default=True,
        help=h_vol_extras,
    )
    parser.add_option("--stats", dest="statsfname", help=h_stats)
    parser.add_option("--statsfile", dest="statsfname", help=h_stats)
    parser.add_option("--subdir", dest="subdir", help=h_subdir)
    parser.add_option(
        "-d",
        "--delimiter",
        dest="delimiter",
        choices=("comma", "tab", "space", "semicolon"),
        default="tab",
        help=h_deli,
    )
    parser.add_option(
        "",
        "--transpose",
        action="store_true",
        dest="transposeflag",
        default=False,
        help=h_tr,
    )
    parser.add_option(
        "", "--etiv", action="store_true", dest="etivflag", default=False, help=h_etiv
    )
    parser.add_option(
        "--skip", action="store_true", dest="skipflag", default=False, help=h_skip
    )
    parser.add_option(
        "-v",
        "--debug",
        action="store_true",
        dest="verboseflag",
        default=False,
        help=h_v,
    )
    parser.add_option(
        "", "--scale", action="store", dest="scale", type="float", help=h_scale
    )
    parser.add_option(
        "--replace53",
        action="store_true",
        dest="replace53",
        help="replace 5.3 structure names with later names",
    )

    (options, args) = parser.parse_args(args)

    if options.SUBJECTS_DIR is not None:
        os.environ["SUBJECTS_DIR"] = options.SUBJECTS_DIR

    # extensive error checks
    if options.subjects is not None:
        if len(options.subjects) < 1:
            print("ERROR: subjects are not specified (use --subjects SUBJECTS)")
            sys.exit(1)
        else:
            options.dodirect = False

    if options.inputs is not None:
        if len(options.inputs) < 1:
            print("ERROR: inputs are not specified")
            sys.exit(1)
        else:
            options.dodirect = True

    if (
        options.subjectsfile is not None
        or options.qdec is not None
        or options.qdeclong is not None
        or options.fsgd is not None
    ):
        options.dodirect = False

    if (
        options.subjects is None
        and options.inputs is None
        and options.subjectsfile is None
        and options.qdec is None
        and options.qdeclong is None
        and options.fsgd is None
    ):
        print(
            "ERROR: Specify one of --subjects, --inputs, --subjectsfile --qdec or --qdec-long"
        )
        print("       or run with --help for help.")
        sys.exit(1)

    count = 0
    if options.subjects is not None:
        count = count + 1
    if options.inputs is not None:
        count = count + 1
    if options.subjectsfile is not None:
        count = count + 1
    if options.qdec is not None:
        count = count + 1
    if options.qdeclong is not None:
        count = count + 1
    if options.fsgd is not None:
        count = count + 1
    if count > 1:
        print(
            "ERROR: Please specify just one of  --subjects, --inputs --subjectsfile --qdec or --qdec-long."
        )
        sys.exit(1)

    if not options.outputfile:
        print("ERROR: output table name should be specified (use --tablefile FILE)")
        sys.exit(1)

    if options.segidsfile is not None and options.segnos is not None:
        print("ERROR: cannot spec both --segids-from-file and --segnos. Spec just one")
        sys.exit(1)

    if options.maxsegno and int(options.maxsegno) < 1:
        print("ERROR: maximum number of segs reported shouldnt be less than 1")
        sys.exit(1)

    if options.segnos is not None and len(options.segnos) < 1:
        print("ERROR: segmentation numbers should be specified with that option")
        sys.exit(1)

    if options.no_segnos is not None and len(options.no_segnos) < 1:
        print(
            "ERROR: to be excluded segmentation numbers should be specified with that option"
        )
        sys.exit(1)

    # parse the segids file
    if options.segidsfile is not None:
        try:
            f = open(options.segidsfile, "r")
            options.segnos = [line.strip() for line in f]
        except IOError:
            print("ERROR: cannot read " + options.segidsfile)
            sys.exit(1)

    if options.verboseflag:
        l.setLevel(logging.DEBUG)

    return options


"""
Args:
    the parsed options
Returns:
    a sequence of tuples ( see below)
assemble_inputs takes the command line parsed options and gives a sequence of tuples.
The tuples take the following format
((specifier1, path1),
 (specifier2, path2),
 ...
 )
where specifierN is the name which goes in the first row of the table. 
This is not necessarily the subject name because in case --inputs arg is given, 
we should output just the number of the input
pathN is the corresponding path where that stat file can be found
"""


def assemble_inputs(o):
    specs_paths = []
    # in the case of --inputs specification
    if o.dodirect:
        for count, inp in enumerate(o.inputs):
            specs_paths.append((str(count), inp))
    # in the case of --subjects spec or --subjectsfile spec
    else:
        # check subjects dir
        subjdir = fsutils.check_subjdirs()
        print("SUBJECTS_DIR : %s" % subjdir)
        if o.subdir is None:
            o.subdir = "stats"
        if o.statsfname is None:
            o.statsfname = "aseg.stats"
        # in case the user gave --subjectsfile argument
        if o.subjectsfile is not None:
            o.subjects = []
            try:
                sf = open(o.subjectsfile)
                [o.subjects.append(subfromfile.strip()) for subfromfile in sf]
                sf.close()
            except IOError:
                print("ERROR: the file %s doesnt exist" % o.subjectsfile)
                sys.exit(1)
        if o.qdec is not None:
            o.subjects = []
            try:
                f = open(o.qdec, "r")
                dialect = csv.Sniffer().sniff(f.readline())
                f.seek(0)
                reader = csv.DictReader(f, dialect=dialect)
                # o.subjects = [row['fsid'] for row in reader]
                for row in reader:
                    fsid = row["fsid"].strip()
                    if fsid[0] != "#":
                        o.subjects.append(fsid)
                f.close()
            except IOError:
                print("ERROR: the file %s doesnt exist" % o.qdec)
                sys.exit(1)
        if o.qdeclong is not None:
            o.subjects = []
            try:
                f = open(o.qdeclong, "r")
                dialect = csv.Sniffer().sniff(f.readline())
                f.seek(0)
                reader = csv.DictReader(f, dialect=dialect)
                # o.subjects = [(row['fsid']+'.long.'+row['fsid-base']) for row in reader]
                for row in reader:
                    fsid = row["fsid"].strip()
                    if fsid[0] != "#":
                        o.subjects.append(fsid + ".long." + row["fsid-base"].strip())
                f.close()
            except IOError:
                print("ERROR: the file %s doesnt exist" % o.qdeclong)
                sys.exit(1)
        if o.fsgd is not None:
            o.subjects = []
            if not os.path.isfile(o.fsgd):
                print("ERROR: fsgd file %s does not exist" % o.fsgd)
                sys.exit(1)
            with open(o.fsgd, "r") as f:
                for line in f:
                    splitline = line.rstrip().split()
                    if splitline[0].upper() == "INPUT":
                        o.subjects.append(splitline[1])

        for sub in o.subjects:
            specs_paths.append(
                (sub, os.path.join(subjdir, sub, o.subdir, o.statsfname))
            )
    return specs_paths


"""
Args:
make_table2d takes a disorganized table of the form 
(spec1,id_name_map1, measurelist1)
(spec2,id_name_map2, measurelist2)
..
..
specN - either the name of the subject or the number of the stat file
id_name_mapN -  a dict with key[segmentations ids, and values=segmentation names..corresponding to the specN file
measurelistN - list of measures corresponding to the segs
(table is disorganized because lengths of the id_name_mapN ( or  measurelistN ) need not be the same for all N)
and a list of segmentation names segnamelist

Returns:
and returns a proper 2d table ( of datastructure 'Ddict(StableDict)')
with list of specN forming the rows
and seglist forming the columns
and the corresponding measure in table[specN][segidN] 
It also returns the list of specN ( rows ) and seglist(column)

If the specN has no segidN, then the corresponding measure is returned as 0.0


"""


def make_table2d(disorganized_table, segnamelist):
    dt = disorganized_table

    # create an ordered 2d table
    table = fsutils.Ddict(fsutils.StableDict)
    for _spec, _id_name_map, _ml in dt:
        for seg in segnamelist:
            try:
                idindex = _id_name_map.values().index(seg)
                table[_spec][seg] = _ml[idindex]
            except ValueError:
                table[_spec][seg] = 0.0

    return [spec for (spec, i, j) in dt], segnamelist, table


"""
Args:
sanitize_tables takes in a datastructure of the form 
(spec1, id_name_map1, measurelist1)
(spec2, id_name_map2, measurelist2)
..
..
where 
specN - either the name of the subject or the number of the stat file
id_name_mapN - an ordered dict with keys=segmentations ids, and values=seg names corresponding to the specN file
measurelistN - list of measures corresponding to the segs

For a proper 2d tabular structure len(segnamelistN) == len(measurelistN)
And usually this might not be the case because different stats files will have slightly 
different segmentations. 
- If --common-segs is specified, output the intersection of segs
- If --all-segs is specified, output the union of segs ( put 0.0 as measure wherever appropriate )
- If none of the above is specified but still the lengths of the lists are inconsistent, exit gracefully.

Returns:
returns rows, columns, table
rows - the sequence which consists of specifiers ( subjects/statsfile numbers)
columns - the sequence which consists of segmentation names
table -  2d table containing the measure

Special Case:
    There might be some segmentations named "Placeholder_Segmentation". These are segs for which the ids were given by the users..
    but when parsing, the parser wasn't able to find the segmentations in the initial list of .stats files. But it puts their value as 0.
    After parsing all the .stats files, the segmentation names for the ids given by the users should be clearer 
    and this function will attempt to rename the "Placeholder Segmentation" to the proper segmentation name. 
"""


def sanitize_table(options, disorganized_table):
    o = options
    _t = disorganized_table

    l.debug("-" * 40)
    l.debug("Sanitizing the table")
    # first find all the ids with 'Placeholder_Segmentation'
    pl_ids = fsutils.StableDict()
    for _spec, _id_name_map, _measl in _t:
        for _id in _id_name_map.keys():
            if _id_name_map[_id] == "Placeholder_Segmentation":
                pl_ids[_id] = "Placeholder_Segmentation"

    # then find the actual segmentation of the ids which have 'Placeholder_Segmentation'
    # if it can't find, it's an error because the only way something is assigned
    # 'Placeholder_Segmentation' is if the user has requested that segmentation id and error results when
    # parser doesn't encounter that segmentation name and the corresponding measure for that id
    if pl_ids:
        tmp_pl_ids = pl_ids.copy()
        itmp_pl_ids = tmp_pl_ids.iteritems()
        plid, plname = next(itmp_pl_ids)
        try:
            for _spec, _id_name_map, _measl in _t:
                for _id in _id_name_map.keys():
                    if _id == plid:
                        if _id_name_map[plid] != "Placeholder_Segmentation":
                            pl_ids[plid] = _id_name_map[plid]
                            plid, plname = next(itmp_pl_ids)
        except StopIteration:
            pass

        # sanity check
        for plid, plname in pl_ids.iteritems():
            if plname == "Placeholder_Segmentation":
                print(
                    "ERROR: cannot find the corresponding segmentation for the id:"
                    + plid
                    + " you provided"
                )
                print("in any of the .stats files parsed")
                sys.exit(1)

        # now go through the entire disorganized table and replace the ids with 'Placeholder_Segmentation'
        # with the actual segmentations
        for _spec, _id_name_map, _measl in _t:
            for _id in _id_name_map.keys():
                if _id_name_map[_id] == "Placeholder_Segmentation":
                    _id_name_map[_id] = pl_ids[_id]

    # At this point, there are no 'Placeholder_Segmentation's

    # find the union and intersection of segnames
    # init the values
    _union = []
    _specs, _id_name_map, _measl = _t[0]
    intersection = _id_name_map.values()

    for _spec, _id_name_map, _measl in _t:
        segnames = _id_name_map.values()
        _union.append(segnames)
        intersection = fsutils.intersect_order(intersection, segnames)
        l.debug("-" * 20)
        l.debug("Specifier: " + _spec)
        l.debug("Intersection upto now:")
        l.debug(intersection)
    # _union is a list of lists. Make it a flat list ( single list )
    temp_union = [item for sublist in _union for item in sublist]
    union = fsutils.unique_union(temp_union)
    l.debug("-" * 20)
    l.debug("Union:")
    l.debug(union)

    if o.common_flag:
        # write only the common segs ( intersection )
        row, column, table = make_table2d(_t, intersection)
    elif o.all_flag:
        # write all the segs ever encountered
        # if there's no seg for a certain .stats file, write the measure as 0.0
        row, column, table = make_table2d(_t, union)
    # at this point, find whether all segs are equal.
    # if not, error out because all-segs / common-segs is not requested
    elif union == intersection:
        row, column, table = make_table2d(_t, union)
    else:
        print("ERROR: All stat files should have the same segmentations.")
        print(
            (
                "If one or more stats file have different segs from others, "
                "use --common-segs or --all-segs flag depending on the need. "
                "(see help)"
            )
        )
        sys.exit(1)

    return row, column, table


def write_table(options, rows, cols, table):
    """
    Write the table from memory to disk. Initialize the writer class.
    """
    tw = fsutils.TableWriter(rows, cols, table)
    r1c1 = "Measure:%s" % (options.meas)
    tw.assign_attributes(
        filename=options.outputfile,
        row1col1=r1c1,
        delimiter=delimiter2char[options.delimiter],
    )
    if options.transposeflag:
        tw.write_transpose()
    else:
        tw.write()


def main(args=None):
    # Command Line options and error checking done here
    options = options_parse(args)
    l.debug("-- The options you entered --")
    l.debug(options)

    # Assemble the input stats files
    subj_listoftuples = assemble_inputs(options)

    # Init the table in memory
    # is a list containing tuples of the form
    # [(specifier, segidlist, structlist, measurelist),] for all specifiers
    pretable = []

    # Parse the stats files
    print("Parsing the .stats files")
    nmeasures0 = None
    for specifier, filepath in subj_listoftuples:
        try:
            l.debug("-" * 20)
            l.debug("Processing file " + filepath)
            parsed = AsegStatsParser(filepath)
            # segs filter from the command line
            if options.segnos is not None:
                parsed.parse_only(options.segnos)
            if options.no_segnos is not None:
                parsed.exclude_structs(options.no_segnos)
            if options.maxsegno is not None:
                parsed.set_maxsegno(options.maxsegno)
            if options.vol_extras is not True:
                parsed.include_vol_extras = 0
            id_name_map, measurelist = parsed.parse(options.meas)
            if options.replace53:
                list53 = {
                    "Left-Thalamus-Proper": "Left-Thalamus",
                    "Right-Thalamus-Proper": "Right-Thalamus",
                    "CorticalWhiteMatterVol": "CerebralWhiteMatterVol",
                    "lhCorticalWhiteMatterVol": "lhCerebralWhiteMatterVol",
                    "rhCorticalWhiteMatterVol": "rhCerebralWhiteMatterVol",
                }
                for str53, strnew in list53.items():
                    keylist = list(id_name_map.keys())
                    # Seg numbers
                    vallist = list(id_name_map.values())
                    # Seg names
                    if str53 not in vallist:
                        continue
                    k = vallist.index(str53)
                    vallist[k] = strnew
                    zipiterator = zip(keylist, vallist)
                    id_name_map = fsutils.StableDict(zipiterator)
            l.debug("-- Parsed Ids, Names --")
            l.debug(id_name_map)
            l.debug("-- Measures --")
            l.debug(measurelist)
        except BadFileError as e:
            if options.skipflag:
                print("Skipping " + str(e))
                continue
            else:
                print("")
                if not os.path.exists(str(e)):
                    print("ERROR: Cannot find stats file " + str(e))
                else:
                    print(
                        "ERROR: The stats file "
                        + str(e)
                        + " is too small to be a valid statsfile"
                    )
                print(
                    "Use --skip flag to automatically skip bad or missing stats files"
                )
                print("")
                sys.exit(1)
        nmeasures = len(measurelist)
        if nmeasures0 is None:
            nmeasures0 = nmeasures
        if nmeasures != nmeasures0 and not options.common_flag and not options.all_flag:
            print(
                "WARN: %s nmeasures = %d, expecting %d"
                % (specifier, nmeasures, nmeasures0)
            )
        pretable.append((specifier, id_name_map, measurelist))

    # Make sure the table has the same number of cols for all stats files
    # and merge them up, clean them up etc. More in the documentation of the fn.
    print("Building the table..")
    rows, columns, table = sanitize_table(options, pretable)

    if options.etivflag:
        try:
            for row in rows:
                etiv = table[row]["EstimatedTotalIntraCranialVol"]
                for col in columns:
                    if col == "lhSurfaceHoles":
                        continue
                    if col == "rhSurfaceHoles":
                        continue
                    if col == "SurfaceHoles":
                        continue
                    if col == "BrainSegVol-to-eTIV":
                        continue
                    if col == "MaskVol-to-eTIV":
                        continue
                    v = table[row][col]
                    table[row][col] = 100 * v / etiv

        except:
            print("ERROR: --etiv, cannot find EstimatedTotalIntraCranialVol in list")
            sys.exit(1)
    # end etiv scaling

    # Scale table values
    if options.scale:
        for row in rows:
            for col in columns:
                table[row][col] = table[row][col] * options.scale

    # Write this table ( in memory ) to disk.. function uses TableWriter class
    print("Writing the table to %s" % options.outputfile)
    write_table(options, rows, columns, table)

    # always exit with 0 exit code
    # sys.exit(0)


if __name__ == "__main__":
    main()
