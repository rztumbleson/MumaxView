# Ryan Tumbleson
import numpy as np
import glob

from traits.api import HasTraits, Range, String, Instance, Button, \
    on_trait_change, Property, cached_property, Directory
from traitsui.api import View, Item, Group, HSplit, VSplit, DefaultOverride


from mayavi import mlab
from mayavi.core.api import PipelineBase, Source
from mayavi.core.ui.api import MayaviScene, SceneEditor, \
    MlabSceneModel

from mumax_helper_func import convert_ovf_to_numpy


class VectorCuts(HasTraits):
    path = String()
    dir = Directory()
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
    plot_x = Instance(PipelineBase)
    plot_y = Instance(PipelineBase)
    plot_z = Instance(PipelineBase)

    # data source
    vector_field_src = Instance(Source)

    def make_cut(self, axis):
        vcp = mlab.pipeline.vector_cut_plane(self.vector_field_src,
                                             scale_factor=1,
                                             plane_orientation='%s_axes' % axis)
        return vcp

    # Property implementations:
    @cached_property
    def _get_time_steps(self):
        if self.path == '':
            return 1
        return len([np_name for np_name in glob.glob(self.path + '*.npy')]) - 1

    @cached_property
    def _get_dim_x(self):
        if self.path == '':
            return 1
        return np.shape(np.load(self.path + 'm' + '%06d' % self.t + '.npy', 'r'))[3]

    @cached_property
    def _get_dim_y(self):
        if self.path == '':
            return 1
        return np.shape(np.load(self.path + 'm' + '%06d' % self.t + '.npy', 'r'))[2]

    @cached_property
    def _get_dim_z(self):
        if self.path == '':
            return 1
        return np.shape(np.load(self.path + 'm' + '%06d' % self.t + '.npy', 'r'))[1]

    @on_trait_change('scene.activated')
    def display_scene(self):
        # set the background to black
        self.scene.scene.background = (0, 0, 0)
        self.scene.mlab.view()

    @on_trait_change('X, Y, Z')
    def update_plot(self):
        self.scene.disable_render = True
        self.plot_x.implicit_plane.plane.origin = (self.X, 0, 0)
        self.plot_y.implicit_plane.plane.origin = (0, self.Y, 0)
        self.plot_z.implicit_plane.plane.origin = (0, 0, self.Z)
        self.scene.disable_render = False

    @on_trait_change('camX, camY')
    def update_cam(self):
        self.scene.mlab.move(0, self.camX, self.camY)

    @on_trait_change('t')
    def update_time(self):
        self.scene.disable_render = True
        npy_data = np.load(self.path + 'm' + '%06d' % self.t + '.npy', 'r')
        u = npy_data[0].T
        v = npy_data[1].T
        w = npy_data[2].T
        self.vector_field_src.mlab_source.trait_set(u=u, v=v, w=w, scalars=w)
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

    @on_trait_change('dir')
    def load_new_data(self):
        self.scene.disable_render = True
        if self.vector_field_src is not None:
            self.plot_x.actor.actor.visibility = False
            self.plot_y.actor.actor.visibility = False
            self.plot_z.actor.actor.visibility = False

            self.vector_field_src = None
            self.plot_x = None
            self.plot_y = None
            self.plot_z = None

        new_path = self.dir + '/'
        new_t = 0
        convert_ovf_to_numpy(new_path)

        npy_data = np.load(new_path + 'm' + '%06d' % new_t + '.npy', 'r')
        u = npy_data[0].T
        v = npy_data[1].T
        w = npy_data[2].T
        self.vector_field_src = self.scene.mlab.pipeline.vector_field(u, v, w, scalars = w)
        self.plot_x = self.make_cut('x')
        self.plot_y = self.make_cut('y')
        self.plot_z = self.make_cut('z')

        self.path = new_path
        self.t = new_t
        self.make_all_plots_nice()
        self.scene.disable_render = False

    def make_all_plots_nice(self):
        # speed up code slightly
        self.scene.scene.anti_aliasing_frames = 0
        # remove large border around cut plane
        self.plot_x.implicit_plane.widget.enabled = False
        self.plot_y.implicit_plane.widget.enabled = False
        self.plot_z.implicit_plane.widget.enabled = False

        # add color to plots
        self.plot_x.glyph.color_mode = 'color_by_scalar'
        self.plot_y.glyph.color_mode = 'color_by_scalar'
        self.plot_z.glyph.color_mode = 'color_by_scalar'

        # set the background to black
        self.scene.scene.background = (0, 0, 0)

        # set the default camera view
        self.scene.mlab.view(focalpoint=(self.dim_x / 2, self.dim_y / 2, 0))
        self.X = self.dim_x/2
        self.Y = self.dim_y/2
        self.Z = self.dim_z/2
        self.scene.mlab.orientation_axes()

    view = View(HSplit(
        Group(
            Item('scene', editor=SceneEditor(scene_class=MayaviScene),
                 height=700, width=1200, show_label=False)),
        Group(VSplit(
            Group(
                Item('dir', show_label=False),
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
    vc = VectorCuts()
    vc.configure_traits()
