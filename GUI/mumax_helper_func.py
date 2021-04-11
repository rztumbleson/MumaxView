def load_npy_data(path):
    """loads all of the files from the path with the extension .npy and returns them in an ordered dictionary.
        Shape of magnetization data is (3 m vectors, z dim, y dim, x dim)"""
    import glob
    import os
    import numpy as np
    from collections import OrderedDict

    np_vars = OrderedDict ()
    npy_shape = np.shape (np.load (path + 'm000000.npy'))
    print ('File(s) loaded:')
    for np_name in glob.glob (path + '*.npy'):
        print (np_name)
        base = os.path.basename (np_name)
        fname = os.path.splitext (base)[0]
        np_vars[fname] = np.lib.format.open_memmap(np_name, shape=npy_shape)
    return sort_dictionary (np_vars)


def append_npy_data(dict_, path):
    '''loads all of the files from the path with the extension .npy and appends them to the given ordered dictionary.
        Shape of magnetization data is (3 m vectors, x dim, y dim, z dim)
    '''
    import glob
    import numpy as np

    print ('File(s) loaded:')
    for np_name in glob.glob (path + '*.npy'):
        print (np_name)
        val = '%06d' % (int (list (dict_)[-1][1:]) + 1)
        dict_['m' + val] = np.lib.format.open_memmap (np_name)
    return dict_


def sort_dictionary(dict_):
    '''Sorts a dictionary based on the key'''
    from collections import OrderedDict

    return OrderedDict (sorted (dict_.items ()))


def read_mumax3_table(filename):
    """Puts the mumax3 output table in a pandas dataframe"""
    from pandas import read_table

    table = read_table (filename)
    table.columns = ' '.join (table.columns).split ()[1::2]
    return table

