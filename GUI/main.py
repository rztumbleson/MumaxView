# Ryan Tumbleson
import numpy as np
import glob

from traits.api import HasTraits, Range, String, Instance, Button, \
    on_trait_change, Property, cached_property
from traitsui.api import View, Item, Group, HSplit, VSplit, DefaultOverride

from mayavi import mlab
from mayavi.core.api import PipelineBase, Source
from mayavi.core.ui.api import MayaviScene, SceneEditor, \
    MlabSceneModel


class VectorCuts(HasTraits):
    path = String()

    time_steps = Property(depends_on='path')
    dim_x = Property(depends_on='path')
    dim_y = Property(depends_on='path')
    dim_z = Property(depends_on='path')

    # set up the scene to be viewed
    scene = Instance(MlabSceneModel, ())

    # Sliders
    X = Range(0, 'dim_x', 'dim_x/2', mode='slider')
    Y = Range(0, 'dim_y', 'dim_y/2', mode='slider')
    Z = Range(0, 'dim_z', 'dim_z/2', mode='slider')
    t = Range(0, 'time_steps', 0, mode='slider')
    cam_slider = Range(1, 20, 1, mode='slider')
    camX_button_pos = Button(label='+X')
    camX_button_neg = Button(label='-X')
    camY_button_pos = Button(label='+Y')
    camY_button_neg = Button(label='-Y')
    resetCam = Button(label='Reset Camera')

    # modules
    plotx = Instance(PipelineBase)
    ploty = Instance(PipelineBase)
    plotz = Instance(PipelineBase)

    # data source
    vector_field_src = Instance(Source)

    # Default values
    def _vector_field_src_default(self):
        npy_data = np.load(self.path + 'm' + '%06d' % self.t + '.npy')
        return self.scene.mlab.pipeline.vector_field(npy_data[0].T, npy_data[1].T,
                                                     npy_data[2].T, scalars=npy_data[2].T)

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
        return len([np_name for np_name in glob.glob(path + '*.npy')]) - 1

    @cached_property
    def _get_dim_x(self):
        return np.shape(np.load(self.path + 'm' + '%06d' % self.t + '.npy'))[3]

    @cached_property
    def _get_dim_y(self):
        return np.shape(np.load(self.path + 'm' + '%06d' % self.t + '.npy'))[2]

    @cached_property
    def _get_dim_z(self):
        return np.shape(np.load(self.path + 'm' + '%06d' % self.t + '.npy'))[1]

    @on_trait_change('scene.activated')
    def display_scene(self):
        self.make_all_plots_nice()

    @on_trait_change('X, Y, Z')
    def update_plot(self):
        self.scene.disable_render = True
        self.plotx.implicit_plane.plane.origin = (self.X, 0, 0)
        self.ploty.implicit_plane.plane.origin = (0, self.Y, 0)
        self.plotz.implicit_plane.plane.origin = (0, 0, self.Z)
        self.scene.disable_render = False

    @on_trait_change('camX, camY')
    def update_cam(self):
        self.scene.mlab.move(0, self.camX, self.camY)

    @on_trait_change('t')
    def update_time(self):
        self.scene.disable_render = True
        npy_data = np.load(self.path + 'm' + '%06d' % self.t + '.npy')
        self.vector_field_src.mlab_source.trait_set(u=npy_data[0].T, v=npy_data[1].T,
                                                    w=npy_data[2].T, scalars=npy_data[2].T)
        self.scene.disable_render = False

    @on_trait_change('resetCam')
    def reset_camera(self):
        self.scene.mlab.view(focalpoint=(self.dim_x/2, self.dim_y/2, 0))

    @on_trait_change('camX_button_neg')
    def button_x_neg(self):
        self.scene.mlab.move(0, self.cam_slider, 0)

    @on_trait_change('camX_button_pos')
    def button_x_pos(self):
        self.scene.mlab.move(0, -1 * self.cam_slider, 0)

    @on_trait_change('camY_button_neg')
    def button_y_neg(self):
        self.scene.mlab.move(0, 0, self.cam_slider)

    @on_trait_change('camY_button_pos')
    def button_y_pos(self):
        self.scene.mlab.move(0, 0, -1 * self.cam_slider)

    def make_all_plots_nice(self):
        # speed up code slightly
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
        self.scene.mlab.view(focalpoint=(self.dim_x/2, self.dim_y/2, 0))
        self.scene.mlab.orientation_axes()

    view = View(HSplit(
        Group(
            Item('scene', editor=SceneEditor(scene_class=MayaviScene),
                 height=700, width=1200, show_label=False)),
        Group(VSplit(
            Group(
                Item('X'),
                Item('Y'),
                Item('Z'),
                Item('t'),
                Item('_'),
                Item('resetCam', show_label=False, full_size=True),
                Item('camY_button_pos', show_label=False),
                Item('camY_button_neg', show_label=False),
                Item('camX_button_pos', show_label=False),
                Item('camX_button_neg', show_label=False),
                Item('cam_slider', show_label=False, editor=DefaultOverride(low_label='fine', high_label='coarse'))
            ),
            )
        )
        ),
        resizable=True,
        title='Vector Field Cuts'
    )


if __name__ == '__main__':
    path = '.\\test data\\' #100,000kB
    vc = VectorCuts(path=path)
    vc.configure_traits()
