# -*- coding:utf-8 -*-
# Created on 10 juin 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright ©2013 Clément Schaff, Mahdi Ben Jelloul, Jérôme Santoul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)
# # # OpenFisca

import logging
from numpy import dtype
from pandas import Series


log = logging.getLogger(__name__)


def assert_dtype(series, dtype_string):
    assert isinstance(series, Series), "First argument is not of Series type"
    assert series.dtype == dtype(dtype_string), "Series {} dtype is {} instead of {}".format(
        series.name, series.dtype, dtype_string)


def assert_variable_in_range(name, wrange, table):
    '''
    Assert if transformed variables are in correct range
    wrange is a list like [minimum, maximum]
    '''
    temp = (table[table[name].notnull()])
    range_1 = wrange[0]
    range_2 = wrange[1]
    for v in temp[name]:
        assert v in range(range_1, range_2), 'some non-null values for %s not in wanted %s: %s' % (
            name, str(wrange), str(v))


def count_NA(name, table):
    '''Counts the number of Na's in a specified axis'''
    print "count of NA's for %s is %s" % (name, str(sum(table[name].isnull())))


def id_formatter(dataframe, entity_id):
    id_unique = dataframe[entity_id].unique()
    new_id_by_old_id = dict(zip(id_unique, range(len(id_unique))))
    dataframe[entity_id] = dataframe[entity_id].replace(to_replace = new_id_by_old_id)
    return dataframe


def print_id(df):
    try:
        print "Individus : ", len(df.noindiv), "/", len(df)
    except:
        print "No noindiv"

    try:
        # Ici, il doit y avoir autant de vous que d'idfoy
        print "Foyers", len(df.idfoy)
        print df["quifoy"].value_counts()
        if df["idfoy"].isnull().any():
            print "NaN in idfoy : ", df["idfoy"].isnull().sum()
        if df["quifoy"].isnull().any():
            print "NaN in quifoy : ", df["quifoy"].isnull().sum()
    except:
        print "No idfoy or quifoy"

    try:
        # Ici, il doit y avoir autant de quimen = 0 que d'idmen
        print "Ménages", len(df.idmen)
        print df["quimen"].value_counts()
        if df["idmen"].isnull().any():
            print "NaN in idmen : ", df["idmen"].isnull().sum()
        if df["quimen"].isnull().any():
            print "NaN in quimen : ", df["quimen"].isnull().sum()
    except:
        print "No idmen or quimen"

    try:
        # Ici, il doit y avoir autant de quifam = 0 que d'idfam
        print "Familles", len(df.idfam)
        print df["quifam"].value_counts()
        if df["idfam"].isnull().any():
            print "NaN in idfam : ", df["idfam"].isnull().sum()
        if df["quifam"].isnull().any():
            print "NaN in quifam : ", df["quifam"].isnull().sum()
    except:
        print "No idfam or quifam"


def control(dataframe, verbose = False, verbose_columns = None, debug = False, verbose_length = 5, ignore = None):
    """
    Function to help debugging the data crunchin' files.

    Parameters
    ---------
    verbose: Default False
    Indicates whether to print the dataframe itself or just perform reguler checks.

    verbose_columns: List
    The columns of the dataframe to print

    verbose_length: Int
    the number of rows to print
    """
    std_list = ['idfoy', 'quifoy', 'idmen', 'quimen', 'idfam', 'quifam']
    for var in std_list:
        try:
            assert var in dataframe.columns
        except:
            raise Exception('the dataframe does not contain the required column %s' % var)

    print 'longueur de la data frame =', len(dataframe.index)
    if debug:
        print 'nb de doublons', len(dataframe[dataframe.duplicated()])
        print 'nb de doublons idfoy/quifoy', len(dataframe[dataframe.duplicated(cols=['idfoy', 'quifoy'])])
        print 'nb de doublons idmen/quimen', len(dataframe[dataframe.duplicated(cols=['idmen', 'quimen'])])
        print 'nb de doublons idfam/quifam', len(dataframe[dataframe.duplicated(cols=['idfam', 'quifam'])])

    if not(debug):
        assert not(dataframe.duplicated().any()), 'présence de lignes en double dans la dataframe'
        assert ~(dataframe.duplicated(cols=['idfoy', 'quifoy'])).all(), 'duplicate of tuple idfoy/quifoy'
        assert ~(dataframe.duplicated(cols=['idmen', 'quimen'])).all(), 'duplicate of tuple idmen/quimen'
        assert ~(dataframe.duplicated(cols=['idfam', 'quifam'])).all(), 'duplicate of tupli idfam/quifam'

    empty_columns = []
    for col in dataframe.columns:
        if (dataframe[col].isnull().all()):
                empty_columns.append(col)

    if empty_columns != []:
        print 'liste des colonnes entièrement vides', empty_columns

    if verbose is True:
        print '------ informations détaillées -------'
        print_id(dataframe)

        if verbose_columns is None:
#             print dataframe.head(verbose_length)
            if dataframe.duplicated().any():
                print dataframe[dataframe.duplicated()].head(verbose_length).to_string()

        else:
            if dataframe.duplicated(verbose_columns).any():
                print 'nb lignes lignes dupliquées_____', len(dataframe[dataframe.duplicated(verbose_columns)])
                print dataframe.loc[:, verbose_columns].describe()
            for col in verbose_columns:
                print 'nombre de NaN dans %s : ' % (col), dataframe[col].isnull().sum()
            print 'colonnes contrôlées ------>', verbose_columns
    print 'vérifications terminées'


def check_structure(df):

    duplicates = df.noindiv.duplicated().sum()
    if duplicates > 1:
        log.warning("there are {} duplicated individuals".format(duplicates))
        df.drop_duplicates("noindiv", inplace = True)

    for entity in ["men", "fam", "foy"]:
        log.info("Checking entity {}".format(entity))
        role = 'qui' + entity
        entity_id = 'id' + entity

        if df[role].isnull().any():
            print "there are NaN in qui{}".format(entity)

        max_entity = df[role].max().astype("int")
        for position in range(0, max_entity + 1):
            test = df[[role, entity_id]].groupby(by = entity_id).agg(lambda x: (x == position).sum())
            errors = (test[role] > 1).sum()
            if errors > 0:
                print "There are %s duplicated qui%s = %s" % (errors, entity, position)


def rectify_dtype(dataframe):
    series_to_rectify = []
    rectified_series = []
    for serie_name, serie in dataframe.iteritems():
        if serie.dtype.char == 'O':  # test for object
            series_to_rectify.append(serie_name)
            print """
Variable name: {}
NaN are present : {}
{}""".format(serie_name, serie.isnull().sum(), serie.value_counts())
            # bool
            if serie.dropna().isin([True, False]).all():
                if serie.isnull().any():
                    serie = serie.fillna(False).copy()
                dataframe[serie_name] = serie.astype('bool', copy = True)
                rectified_series.append(serie_name)
            # Nombre 01-99
            elif serie.dropna().str.match("\d\d$").all():
                if serie.isnull().any():
                    serie = serie.fillna(0)
                dataframe[serie_name] = serie.astype('int', copy = True)
                rectified_series.append(serie_name)
            # year
            elif serie_name in ['birthvous', 'birthconj', 'caseH']:
                if serie.isnull().any():
                    serie = serie.fillna(9999)
                dataframe[serie_name] = serie.astype('int', copy = True)
                rectified_series.append(serie_name)
            # datetime
            elif serie_name[0:4] == "date":
                from pandas import to_datetime
                dataframe[serie_name] = to_datetime(
                    serie.str[:2] + "-" + serie.str[2:4] + "-" + serie.str[4:8],
                    coerce = True)
                rectified_series.append(serie_name)

            if serie_name in rectified_series:
                print """Converted to {}
{}""".format(dataframe[serie_name].dtype, dataframe[serie_name].value_counts())

    print set(series_to_rectify).difference(rectified_series)
