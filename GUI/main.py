# Ryan Tumbleson
def load_npy_data(path):
    '''loads all of the files from the path with the extension .npy and returns them in an ordered dictionary.
        Shape of magnetization data is (3 m vectors, z dim, y dim, x dim)'''
    import glob
    import os
    import numpy as np
    from collections import OrderedDict

    np_vars = OrderedDict()
    print('File(s) loaded:')
    for np_name in glob.glob(path + '*.npy'):
        print(np_name)
        base = os.path.basename(np_name)
        fname = os.path.splitext(base)[0]
        np_vars[fname] = np.load(np_name, 'r')
    return sort_dictionary(np_vars)


def append_npy_data(dict_, path):
    '''loads all of the files from the path with the extension .npy and appends them to the given ordered dictionary.
        Shape of magnetization data is (3 m vectors, x dim, y dim, z dim)
    '''
    import glob
    import numpy as np

    print('File(s) loaded:')
    for np_name in glob.glob(path + '*.npy'):
        print(np_name)
        val = '%06d' % (int(list(dict_)[-1][1:]) + 1)
        dict_['m' + val] = np.lib.format.open_memmap(np_name)
    return dict_


def sort_dictionary(dict_):
    '''Sorts a dictionary based on the key'''
    from collections import OrderedDict

    return OrderedDict(sorted(dict_.items()))


def read_mumax3_table(filename):
    """Puts the mumax3 output table in a pandas dataframe"""
    from pandas import read_table

    table = read_table(filename)
    table.columns = ' '.join(table.columns).split()[1::2]
    return table


from traits.api import HasTraits, Range, Dict, List, Instance, Button, \
        on_trait_change
from traitsui.api import View, Item, Group, HSplit

from mayavi import mlab
from mayavi.core.api import PipelineBase, Source
from mayavi.core.ui.api import MayaviScene, SceneEditor, \
                MlabSceneModel


class VectorCuts(HasTraits):
    # force the data to be a dictionary
    data = Dict()
    keys = List()
    # set up the scene to be viewed
    scene = Instance(MlabSceneModel, ())

    # Sliders
    X = Range(0, 512, 256, mode='slider')
    Y = Range(0, 512, 256, mode='slider')
    Z = Range(0, 33, 10, mode='slider')
    t = Range(0, 100, 0, mode='slider')
    camX = Range(-1000, 1000, 256, mode='slider')
    camY = Range(-1000, 1000, 256, mode='slider')
    camZ = Range(-1000, 1000, 0, mode='slider')
    resetCam = Button(label='Reset Camera')

    # modules
    plotx = Instance(PipelineBase)
    ploty = Instance(PipelineBase)
    plotz = Instance(PipelineBase)

    # data source
    vector_field_src = Instance(Source)

    # Default values
    def _vector_field_src_default(self):
        self.keys = list(self.data.keys())
        return mlab.pipeline.vector_field(self.data[self.keys[0]][0].T, self.data[self.keys[0]][1].T,
                                          self.data[self.keys[0]][2].T, scalars=self.data[self.keys[0]][2].T)

    def make_cut(self, axis):
        vcp = mlab.pipeline.vector_cut_plane(self.vector_field_src,
                                             mask_points=1,
                                             scale_factor=1,
                                             plane_orientation='%s_axes' % axis)
        return vcp

    def _plotx_default(self):
        return self.make_cut('x')

    def _ploty_default(self):
        return self.make_cut('y')

    def _plotz_default(self):
        return self.make_cut('z')

    @on_trait_change('scene.activated')
    def display_scene(self):
        self.make_all_plots_nice()

    @on_trait_change('X, Y, Z, camX, camY, camZ')
    def update_plot(self):
        self.plotx.implicit_plane.plane.origin = (self.X, self.camY, self.camZ)
        self.ploty.implicit_plane.plane.origin = (self.camX, self.Y, self.camZ)
        self.plotz.implicit_plane.plane.origin = (self.camX, self.camY, self.Z)

        self.scene.mlab.view(focalpoint=(self.camX, self.camY, self.camZ))

    @on_trait_change('t')
    def update_time(self):
        self.plotx.mlab_source.trait_set(u=self.data[self.keys[self.t]][0].T, v=self.data[self.keys[self.t]][1].T,
                                         w=self.data[self.keys[self.t]][2].T, scalars=self.data[self.keys[self.t]][2].T)
        self.ploty.mlab_source.trait_set(u=self.data[self.keys[self.t]][0].T, v=self.data[self.keys[self.t]][1].T,
                                         w=self.data[self.keys[self.t]][2].T, scalars=self.data[self.keys[self.t]][2].T)
        self.plotz.mlab_source.trait_set(u=self.data[self.keys[self.t]][0].T, v=self.data[self.keys[self.t]][1].T,
                                         w=self.data[self.keys[self.t]][2].T, scalars=self.data[self.keys[self.t]][2].T)

    @on_trait_change('resetCam')
    def reset_camera(self):
        self.scene.mlab.view(focalpoint=(256, 256, 0))
        self.camX = 256
        self.camY = 256
        self.camZ = 0

    def make_all_plots_nice(self):
        # remove large border around cut plane
        self.plotx.implicit_plane.widget.enabled = False
        self.ploty.implicit_plane.widget.enabled = False
        self.plotz.implicit_plane.widget.enabled = False

        # add color to plots
        self.plotx.glyph.color_mode = 'color_by_scalar'
        self.ploty.glyph.color_mode = 'color_by_scalar'
        self.plotz.glyph.color_mode = 'color_by_scalar'

        # set the background to black
        self.scene.scene.background = (0, 0, 0)

        # set the default camera view
        self.scene.mlab.view(focalpoint=(256, 256, 0))

    view = View(HSplit(
        Group(
            Item('scene', editor=SceneEditor(scene_class=MayaviScene),
                 height=700, width=1200, show_label=False)),
        Group(
            Item('X'),
            Item('Y'),
            Item('Z'),
            Item('t'),
            Item('camX'),
            Item('camY'),
            Item('camZ'),
            Item('resetCam', show_label=False)
        ),
    ),
        resizable=True,
        title='Vector Field Cuts'
    )

if __name__ == '__main__':
    path = 'G:\\My Drive\\Steps\\steps10Oe.out\\'
    dataDict = load_npy_data(path)
    dataTable = read_mumax3_table(path + 'table.txt')
    print('Done!')

    vc = VectorCuts(data=dataDict)
    vc.configure_traits()

