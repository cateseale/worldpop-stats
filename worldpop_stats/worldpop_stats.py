import ee
import geemap
import time

ee.Initialize()


def get_worldpop_data_from_gee(constrained: bool = False) -> ee.ImageCollection:
    """
    Gets the WorldPop data hosted by Google Earth Engine as an Image Collection.

    Params:
        - constrained (bool): Flag to use the constrained version. More info at
        https://www.worldpop.org/methods/top_down_constrained_vs_unconstrained/
    Returns:
        - (ee.ImageCollection): Raster collection of world population estimates, broken down by age and sex, at 100m
        resolution.
    """

    if constrained:
        return ee.ImageCollection("WorldPop/GP/100m/pop_age_sex_cons_unadj")
    else:
        return ee.ImageCollection("WorldPop/GP/100m/pop_age_sex")


def worldpop_mosaic(constrained: bool = False) -> ee.Image:
    """
    Creates a global mosaic of WorldPop data.

    Params:
        - constrained (bool): Flag to use the constrained version. More info at
        https://www.worldpop.org/methods/top_down_constrained_vs_unconstrained/
    Returns:
        - pop_data_img (ee.Image): Raster image of world population estimates, broken down by age and sex, at 100m
        resolution.
    """
    pop_data = get_worldpop_data_from_gee(constrained=constrained)
    pop_data_img = pop_data.mosaic()

    return pop_data_img


def worldpop_zonal_stats(shapefile: str,
                         out_path: str = 'output.csv',
                         constrained: bool = False,
                         scale: int = 100):
    """
    For a given shapefile, calculate the total estimated population resident in each polygon area.

    Params:
        - shapefile (str): Path to shapefile of polygons.
        - out_path (str): Export the results to this file, can be csv, shp, json, kml, kmz.
        - constrained (bool): Flag to use the constrained version. More info at
        https://www.worldpop.org/methods/top_down_constrained_vs_unconstrained/
        - scale (int): Worldpop on GEE is at 100m x 100m pixels, so set above 100 for sensible-ish results.
    Returns:
        None
    """

    fc = geemap.shp_to_ee(shapefile)
    worldpop = worldpop_mosaic(constrained=constrained)

    error_template = "An exception of type {0} occurred. Arguments:\n{1!r}"

    try:
        geemap.zonal_statistics(worldpop, fc, out_file_path=out_path, scale=scale, statistics_type='SUM',
                                bestEffort=True)
    except Exception as ex:

        if "Output of image computation is too large" in repr(ex.args):
            print("Computation is too large, trying tileScale=2")

            try:
                geemap.zonal_statistics(worldpop, fc, out_file_path=out_path, scale=scale, statistics_type='SUM',
                                        bestEffort=True, tile_scale=2)
            except Exception as ex:
                if "Output of image computation is too large" in repr(ex.args):
                    print("Computation is too large, trying tileScale=4")

                    try:
                        geemap.zonal_statistics(worldpop, fc, out_file_path=out_path, scale=scale,
                                                statistics_type='SUM', bestEffort=True, tile_scale=4)
                    except Exception as ex:
                        if "Output of image computation is too large" in repr(ex.args):
                            print("The shapefile is too big for the scale. You could try splitting up the shapefile or "
                                  "increasing the scale parameter.")

                        else:
                            message = error_template.format(type(ex).__name__, ex.args)
                            print(message)

                else:
                    message = error_template.format(type(ex).__name__, ex.args)
                    print(message)

        else:
            message = error_template.format(type(ex).__name__, ex.args)
            print(message)


if __name__ == "__main__":
    start_time = time.time()
    worldpop_zonal_stats(shapefile="/Users/cate/git/mapaction-worldpop/data/gmb/gmb_admn_ad2_py_s1_wfp_pp_districts.shp",
                         out_path="/Users/cate/git/worldpop-stats/output.shp",
                         constrained=False,
                         scale=100)
    print("time elapsed: {:.2f}s".format(time.time() - start_time))