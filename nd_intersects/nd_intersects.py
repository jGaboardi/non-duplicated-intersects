"""Demonstrating an enhanced intersect operation with sjoin in GeoPandas
"""

__author__ = "James Gaboardi <jgaboardi@gmail.com>"


import geopandas
import matplotlib
import string
from shapely.geometry import Point, Polygon


def nd_intersects(pnts, pgons, ptid, pgid, keep_columns):
    """Create a non-duplicated intersects geodataframe.
    
    Parameters
    ----------
    pnts : geopandas.GeoDataFrame
        Points for spatial join.
    pgons : geopandas.GeoDataFrame
        Polygons for spatial join.
    how : str
        Type of join to perform.
    ptid : str
        Point ID variable.
    pgid : str
        Polygon ID variable.
    keep_columns : list
        Columns to retain.
    
    Returns
    -------
    ndgdf : geopandas.GeoDataFrame
        Result of the non-duplicated intersects method.
    """

    def _row(_p, _g):
        """generate specific row values for dataframe"""
        return (_p, "-".join(_g[pgid]), *_g.geometry.unique())

    if pnts.geometry.name not in keep_columns:
        keep_columns += [pnts.geometry.name]

    # perform "intersects" spatial join
    igdf = do_sjoin(pnts, pgons, "intersects", ptid, pgid, keep_columns)

    # Create shell dataframe to store squashed intersection points
    ndgdf = geopandas.GeoDataFrame(columns=igdf.columns, index=pnts.index)

    # Populate the squashed intersection points dataframe
    ndgdf.loc[:, keep_columns] = [_row(p, g) for p, g in igdf.groupby(ptid)]

    return ndgdf


def do_sjoin(df1, df2, op, ptid, pgid, keep_columns, how="left", fillna="NaN"):
    """Perform a spatial join in GeoPandas.
    
    Parameters
    ----------
    df1 : geopandas.GeoDataFrame
        Left geodataframe for the spatial join.
    df2 : geopandas.GeoDataFrame
        Right geodataframe for the spatial join.
    op : str
        Binary predicate in Shapley.
        https://shapely.readthedocs.io/en/latest/manual.html#binary-predicates
    ptid : str
        Point ID variable.
    pgid : str
        Polygon ID variable.
    keep_columns : list
        Columns to retain.
    how : str
        Join method. Defaults is 'left'. Also supports {'right', 'inner'}.
    fillna : {None, bool, int, str, ...}
        Any value to fill 'not a value' cells. Defaults is 'NaN'.
    
    Returns
    -------
    df3 : 
        Result of the spatial join.
    """

    # Make sure to keep geometry (from left dataframe)
    if df1.geometry.name not in keep_columns:
        keep_columns += [df1.geometry.name]

    # Perform join
    df3 = geopandas.sjoin(df1, df2, how=how, op=op)[keep_columns]

    # Fill actual NaN with "NaN" for plotting purposes
    df3.loc[(df3[pgid].isna()), pgid] = fillna

    return df3


def demo_plot_join(
    pnts, pgons, ptid, pgid, title, orig, save=None, cmap="Paired", fmat="png"
):
    """Plot the demonstration spatial join.
    
    Parameters
    ----------
    pnts : geopandas.GeoDataFrame
        Points for spatial join.
    pgons : geopandas.GeoDataFrame
        Polygons for spatial join.
    ptid : str
        Point ID variable.
    pgid : str
        Polygon ID variable.
    title : str
        Supertitle of the plot.
    orig : int
        Set cardinality of original point set, $|P|$.
    save : str
        File name (including path) plot output. Default is None.
    figsize : tuple
        Figure size. Default is (8,8).
    cmap : str
        Default is 'Paired'.
        https://matplotlib.org/3.1.1/gallery/color/colormap_reference.html
    fmat : str
        Format for saving `savefig`. Default is 'png'.
    """

    def pgon_labels(p):
        """label polygons"""

        def _loc(_x):
            """polygon label location helper"""
            return [coord + 0.35 for coord in _x.geometry.centroid.coords[0]]

        kws = {"size": 25, "va": "bottom"}
        p.apply(lambda x: base.annotate(s=x[pgid], xy=_loc(x), **kws), axis=1)

    def pt_labels(p):
        """label points with PTID+PGID"""

        def _lab(_x):
            """point label helper"""
            return ",".join([_x[ptid], _x[pgid]])

        def _loc(_x):
            """point label location helper"""
            return _x.geometry.coords[0]

        kws = {"size": 15, "va": "bottom", "weight": "bold"}
        p.apply(lambda x: base.annotate(s=_lab(x), xy=_loc(x), **kws), axis=1)

    def add_title(label, sup=True):
        """add a suptitle or title"""
        if sup:
            matplotlib.pyplot.suptitle(label, x=0.515, y=0.98, fontsize=30)
        else:
            matplotlib.pyplot.title(label, fontsize=20)

    def set_card():
        """Determine equality of set cardinality for subtitle"""
        sj_pnts = pnts.shape[0]
        if orig == sj_pnts:
            oper = "="
        elif orig < sj_pnts:
            oper = "<"
        elif orig > sj_pnts:
            oper = ">"
        else:
            raise ValueError("Equality could not be determined.")
        return "$\\vert P \\vert %s \\vert P^\\prime \\vert$" % oper

    base = pgons.plot(figsize=(8,8), zorder=0, facecolor="w", edgecolor="k")
    pnts.plot(ax=base, markersize=50, column=pgid, cmap=cmap)

    # polygons labels
    pgon_labels(pgons)
    # points labels
    pt_labels(pnts)
    # add title
    add_title(title)
    # add subtitle
    add_title(set_card(), sup=False)
    # save figure
    if save:
        kws = {"bbox_inches": "tight", "format": fmat, "dpi": 400, "quality": 100}
        matplotlib.pyplot.savefig("%s.%s" % (save, fmat), **kws)


def demo_points(ptid):
    """Points for demo"""
    point_coords = [
        (-1, -1),
        (0, -1),
        (0.5, -0.75),
        (-0.5, -0.5),
        (0.5, -0.5),
        (0, 0),
        (0.5, 0.5),
    ]
    point_ids = {ptid: list(string.ascii_uppercase[: len(point_coords)])}
    points = [Point(coords) for coords in point_coords]
    points = geopandas.GeoDataFrame(point_ids, geometry=points)
    return points


def demo_polygons(pgid):
    """Polygons for demo"""
    polygon_coords = [
        [(-1, -1), (0, -1), (0, 0), (-1, 0)],
        [(0, -1), (1, -1), (1, 0), (0, 0)],
        [(-1, 0), (0, 0), (0, 1), (-1, 1)],
    ]
    polygons = [Polygon(coords) for coords in polygon_coords]
    polygon_ids = {pgid: list(string.ascii_lowercase[-len(polygon_coords) :])}
    polygons = geopandas.GeoDataFrame(polygon_ids, geometry=polygons)
    return polygons


def demo():
    """Run the demonstration synthetic example"""
    # Variable names
    PTID = "point_id"
    PGID = "polygon_id"
    KEEP_COLUMNS = [PTID, PGID]
    # Synthetic geometries
    points = demo_points(ptid=PTID)
    polygons = demo_polygons(pgid=PGID)
    # Within
    print("* Join: %s\n" % "within")
    print(do_sjoin(points, polygons, "within", PTID, PGID, KEEP_COLUMNS))
    print("------------------------------------------------------\n")
    # Intersects
    print("* Join: %s\n" % "intersects")
    print(do_sjoin(points, polygons, "intersects", PTID, PGID, KEEP_COLUMNS))
    print("------------------------------------------------------\n")
    # Non-duplicated intersects
    print("* Join: n-d intersects")
    print(nd_intersects(points, polygons, PTID, PGID, KEEP_COLUMNS))
    print("------------------------------------------------------\n")


if __name__ == "__main__":
    demo()
