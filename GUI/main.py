# Ryan Tumbleson
import PyQt5
import numpy as np

from mumax_helper_func import *
from traits.api import HasTraits, Range, Dict, List, Instance, Button, \
        on_trait_change, Property, cached_property
from traitsui.api import View, Item, Group, HSplit

from mayavi import mlab
from mayavi.core.api import PipelineBase, Source
from mayavi.core.ui.api import MayaviScene, SceneEditor, \
                MlabSceneModel

class VectorCuts(HasTraits):
    # force the data to be a dictionary
    data = Dict()
    keys = List()
    time_steps = Property(depends_on='data')
    dim_x = Property(depends_on='data')
    dim_y = Property(depends_on='data')
    dim_z = Property(depends_on='data')

    # set up the scene to be viewed
    scene = Instance(MlabSceneModel, ())

    # Sliders
    X = Range(0, 'dim_x', 'dim_x/2', mode='slider')
    Y = Range(0, 'dim_y', 'dim_y/2', mode='slider')
    Z = Range(0, 'dim_z', 'dim_z/2', mode='slider')
    t = Range(0, 'time_steps', 0, mode='slider')
    camX = Range(-1000, 1000, 256, mode='slider')
    camY = Range(-1000, 1000, 256, mode='slider')
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
        return self.scene.mlab.pipeline.vector_field(self.data[self.keys[0]][0].T, self.data[self.keys[0]][1].T,
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

    # Property implementations:
    @cached_property
    def _get_time_steps(self):
        return len(self.keys)-1

    @cached_property
    def _get_dim_x(self):
        return np.shape(self.data[self.keys[0]][0].T)[0]

    @cached_property
    def _get_dim_y(self):
        return np.shape(self.data[self.keys[0]][0].T)[1]

    @cached_property
    def _get_dim_z(self):
        return np.shape(self.data[self.keys[0]][0].T)[2]

    @on_trait_change('scene.activated')
    def display_scene(self):
        self.make_all_plots_nice()

    @on_trait_change('X, Y, Z, camX, camY, camZ')
    def update_plot(self):
        self.plotx.implicit_plane.plane.origin = (self.X, self.camY, 0)
        self.ploty.implicit_plane.plane.origin = (self.camX, self.Y, 0)
        self.plotz.implicit_plane.plane.origin = (self.camX, self.camY, self.Z)

        self.scene.mlab.view(focalpoint=(self.camX, self.camY, 0))

    @on_trait_change('t')
    def update_time(self):
        self.vector_field_src.mlab_source.trait_set(u=self.data[self.keys[self.t]][0].T, v=self.data[self.keys[self.t]][1].T,
                                         w=self.data[self.keys[self.t]][2].T, scalars=self.data[self.keys[self.t]][2].T)

    @on_trait_change('resetCam')
    def reset_camera(self):
        self.scene.mlab.view(focalpoint=(256, 256, 0))
        self.camX = 256
        self.camY = 256

    def make_all_plots_nice(self):
        self.scene.scene.anti_aliasing_frames = 0
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
        self.scene.mlab.orientation_axes()

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
            Item('resetCam', show_label=False)
        ),
    ),
        resizable=True,
        title='Vector Field Cuts'
    )

if __name__ == '__main__':
    ETS_TOOLKIT = PyQt5
    path = 'G:\\My Drive\\Steps\\steps10Oe.out\\'

    dataDict = load_npy_data(path)
    #dataTable = read_mumax3_table(path + 'table.txt')
    print('Done!')

    vc = VectorCuts(data=dataDict)
    vc.configure_traits()