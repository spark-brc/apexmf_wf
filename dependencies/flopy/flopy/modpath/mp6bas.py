"""
mpbas module.  Contains the ModpathBas class. Note that the user can access
the ModpathBas class as `flopy.modflow.ModpathBas`.

Additional information for this MODFLOW/MODPATH package can be found at the `Online
MODFLOW Guide
<https://water.usgs.gov/ogw/modflow/MODFLOW-2005-Guide/bas6.html>`_.

"""
import numpy as np

from ..pakbase import Package
from ..utils import Util2d, Util3d


class Modpath6Bas(Package):
    """
    MODPATH Basic Package Class.

    Parameters
    ----------
    model : model object
        The model object (of type :class:`flopy.modpath.mp.Modpath`) to which
        this package will be added.
    hnoflo : float
        Head value assigned to inactive cells (default is -9999.).
    hdry : float
        Head value assigned to dry cells (default is -8888.).
    def_face_ct : int
        Number fo default iface codes to read (default is 0).
    bud_label : str or list of strs
        MODFLOW budget item to which a default iface is assigned.
    def_iface : int or list of ints
        Cell face (iface) on which to assign flows from MODFLOW budget file.
    laytyp : None, int or list of ints
        MODFLOW layer type (0 is convertible, 1 is confined). If None, read from modflow model
    ibound : None or array of ints, optional
        The ibound array (the default is 1). If None, pull from parent modflow model
    prsity : array of ints, optional
        The porosity array (the default is 0.30).
    prsityCB : array of ints, optional
        The porosity array for confining beds (the default is 0.30).
    extension : str, optional
        File extension (default is 'mpbas').

    Attributes
    ----------
    heading : str
        Text string written to top of package input file.

    Methods
    -------

    See Also
    --------

    Notes
    -----

    Examples
    --------

    >>> import flopy
    >>> m = flopy.modpath.Modpath6()
    >>> mpbas = flopy.modpath.Modpath6Bas(m)

    """

    def __init__(
        self,
        model,
        hnoflo=-9999.0,
        hdry=-8888.0,
        def_face_ct=0,
        bud_label=None,
        def_iface=None,
        laytyp=None,
        ibound=None,
        prsity=0.30,
        prsityCB=0.30,
        extension="mpbas",
        unitnumber=86,
    ):
        super().__init__(model, extension, "MPBAS", unitnumber)
        nrow, ncol, nlay, nper = self.parent.nrow_ncol_nlay_nper
        self.heading1 = "# MPBAS for Modpath, generated by Flopy."
        self.heading2 = "#"
        self.hnoflo = hnoflo
        self.hdry = hdry
        self.def_face_ct = def_face_ct
        self.bud_label = bud_label
        self.def_iface = def_iface
        self.laytyp = self._create_ltype(laytyp)
        if ibound is None:
            mf = self.parent.getmf()
            if mf is None:
                raise ValueError(
                    "either ibound must be passed or modflowmodel must not be None"
                )
            else:
                bas = mf.get_package("BAS6")
                if bas is not None:
                    ibound = bas.ibound.array
                else:
                    raise ValueError("could not get bas6 package from modflow")
        ibound = Util3d(
            model,
            (nlay, nrow, ncol),
            np.int32,
            ibound,
            name="ibound",
            locat=self.unit_number[0],
        )

        self.ibound = ibound
        self.prsity = prsity
        self.prsityCB = prsityCB
        self.prsity = Util3d(
            model,
            (nlay, nrow, ncol),
            np.float32,
            prsity,
            name="prsity",
            locat=self.unit_number[0],
        )
        self.prsityCB = Util3d(
            model,
            (nlay, nrow, ncol),
            np.float32,
            prsityCB,
            name="prsityCB",
            locat=self.unit_number[0],
        )
        self.parent.add_package(self)

    def write_file(self):
        """
        Write the package file

        Returns
        -------
        None

        """
        # Open file for writing
        f_bas = open(self.fn_path, "w")
        f_bas.write(f"#{self.heading1}\n#{self.heading2}\n")
        f_bas.write(f"{self.hnoflo:16.6f} {self.hdry:16.6f}\n")
        f_bas.write(f"{self.def_face_ct:4d}\n")
        if self.def_face_ct > 0:
            for i in range(self.def_face_ct):
                f_bas.write(f"{self.bud_label[i]:20s}\n")
                f_bas.write(f"{self.def_iface[i]:2d}\n")
        # f_bas.write('\n')

        # need to reset lc fmtin
        lc = self.laytyp
        lc.set_fmtin("(40I2)")
        f_bas.write(lc.string)
        # from modpath bas--uses keyword array types
        f_bas.write(self.ibound.get_file_entry())
        # from MT3D bas--uses integer array types
        # f_bas.write(self.ibound.get_file_entry())
        f_bas.write(self.prsity.get_file_entry())
        f_bas.write(self.prsityCB.get_file_entry())

        f_bas.close()

    def _create_ltype(self, laytyp):
        lc = None
        nrow, ncol, nlay, nper = self.parent.nrow_ncol_nlay_nper
        if laytyp is not None:  # user passed layertype
            lc = Util2d(
                self.parent,
                (nlay,),
                np.int32,
                laytyp,
                name="bas - laytype",
                locat=self.unit_number[0],
            )

        else:  # no user passed layertype
            have_layertype = False
            if self.parent.getmf() is None:
                raise ValueError(
                    "if modflowmodel is None then laytype must be passed"
                )

            # run though flow packages
            flow_package = self.parent.getmf().get_package("BCF6")
            if flow_package != None:
                lc = Util2d(
                    self.parent,
                    (nlay,),
                    np.int32,
                    flow_package.laycon.get_value(),
                    name="bas - laytype",
                    locat=self.unit_number[0],
                )
                have_layertype = True

            flow_package = self.parent.getmf().get_package("LPF")
            if flow_package != None and not have_layertype:
                lc = Util2d(
                    self.parent,
                    (nlay,),
                    np.int32,
                    flow_package.laytyp.get_value(),
                    name="bas - laytype",
                    locat=self.unit_number[0],
                )
                have_layertype = True
            flow_package = self.parent.getmf().get_package("UPW")
            if flow_package != None and have_layertype:
                lc = Util2d(
                    self.parent,
                    (nlay,),
                    np.int32,
                    flow_package.laytyp.get_value(),
                    name="bas - laytype",
                    locat=self.unit_number[0],
                )

        assert lc is not None, "could not determine laytype"
        return lc
