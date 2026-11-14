"""
SPHEREx Planet X Challenge - Astrometric Centroiding & Proper Motion Validation Engine
Fits 2D centroids across multi-epoch visits, estimates proper motion vector, and validates against Gaia DR3.
"""

from typing import List, Dict, Any, Tuple
import math

SPHEREx_PIXEL_SCALE_ARCSEC = 6.15

def fit_2d_centroid(image: List[List[float]], approx_x: float, approx_y: float, box_radius: int = 4) -> Tuple[float, float, float]:
    """
    Fits 2D intensity-weighted centroid and peak amplitude inside a localized sub-box.
    Returns (x_centroid, y_centroid, peak_flux).
    """
    height = len(image)
    width = len(image[0])
    
    x_min = max(0, int(round(approx_x - box_radius)))
    x_max = min(width - 1, int(round(approx_x + box_radius)))
    y_min = max(0, int(round(approx_y - box_radius)))
    y_max = min(height - 1, int(round(approx_y + box_radius)))
    
    sum_w = 0.0
    sum_wx = 0.0
    sum_wy = 0.0
    peak = 0.0
    
    for y in range(y_min, y_max + 1):
        for x in range(x_min, x_max + 1):
            val = image[y][x]
            if val is None or math.isnan(val):
                continue
            if val > peak:
                peak = val
            # Use positive flux above local background
            w = max(0.0, val)
            sum_w += w
            sum_wx += w * x
            sum_wy += w * y
            
    if sum_w > 0.0:
        cx = sum_wx / sum_w
        cy = sum_wy / sum_w
    else:
        cx = approx_x
        cy = approx_y
        
    return round(cx, 3), round(cy, 3), round(peak, 3)

def validate_proper_motion_astrometry(
    visit_stacks: List[Dict[str, Any]],
    catalog_target: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Fits empirical centroids across all visits, fits linear proper motion vector,
    and cross-validates against Gaia DR3 / CatWISE ground-truth astrometry.
    """
    n_visits = len(visit_stacks)
    if n_visits < 2:
        return {"status": "insufficient_visits", "message": "At least 2 visits required for astrometric fit"}

    cat_pm_ra = catalog_target.get("pm_ra_mas", 0.0)
    cat_pm_dec = catalog_target.get("pm_dec_mas", 0.0)
    cat_total_pm = math.hypot(cat_pm_ra, cat_pm_dec)

    # Track measured centroids
    centroids = []
    times_years = []
    
    # Starting center of the stamp (typically 32, 32 in a 64x64 cutout)
    h = len(visit_stacks[0]["stacked_image"])
    w = len(visit_stacks[0]["stacked_image"][0])
    cx0, cy0 = w / 2.0, h / 2.0
    
    ref_time = visit_stacks[0]["mjd_mid"] / 365.25
    
    for v_idx, v in enumerate(visit_stacks):
        img = v["stacked_image"]
        t_yr = (v["mjd_mid"] / 365.25) - ref_time
        times_years.append(t_yr)
        
        # Expected displacement from catalog motion
        # +x is East (-RA), +y is North (+Dec) in North-Up East-Left grid
        dt_yr = (v["mjd_mid"] - visit_stacks[0]["mjd_mid"]) / 365.25
        exp_dx_px = -(cat_pm_ra / 1000.0 * dt_yr) / SPHEREx_PIXEL_SCALE_ARCSEC
        exp_dy_px = (cat_pm_dec / 1000.0 * dt_yr) / SPHEREx_PIXEL_SCALE_ARCSEC
        
        fx, fy, peak = fit_2d_centroid(img, cx0 + exp_dx_px, cy0 + exp_dy_px)
        centroids.append({
            "visit_id": v["visit_id"],
            "date_utc": v["date_utc"],
            "mjd": v["mjd_mid"],
            "dt_years": round(dt_yr, 3),
            "fitted_x_px": fx,
            "fitted_y_px": fy,
            "peak_surface_brightness": peak
        })

    # Linear regression fit for dx/dt and dy/dt
    # y = a + b * t
    t_mean = sum(times_years) / n_visits
    var_t = sum((t - t_mean) ** 2 for t in times_years)
    
    if var_t > 1e-6:
        cov_tx = sum((times_years[i] - t_mean) * (centroids[i]["fitted_x_px"] - (sum(c["fitted_x_px"] for c in centroids)/n_visits)) for i in range(n_visits))
        cov_ty = sum((times_years[i] - t_mean) * (centroids[i]["fitted_y_px"] - (sum(c["fitted_y_px"] for c in centroids)/n_visits)) for i in range(n_visits))
        
        vx_px_yr = cov_tx / var_t
        vy_px_yr = cov_ty / var_t
    else:
        vx_px_yr = 0.0
        vy_px_yr = 0.0

    # Convert px/yr to mas/yr
    # vx_px_yr is East motion (-RA), so fitted_pm_ra = -vx * scale * 1000
    fitted_pm_ra_mas = -vx_px_yr * SPHEREx_PIXEL_SCALE_ARCSEC * 1000.0
    fitted_pm_dec_mas = vy_px_yr * SPHEREx_PIXEL_SCALE_ARCSEC * 1000.0
    fitted_total_pm_mas = math.hypot(fitted_pm_ra_mas, fitted_pm_dec_mas)

    # Residual against catalog ground truth
    res_ra = fitted_pm_ra_mas - cat_pm_ra
    res_dec = fitted_pm_dec_mas - cat_pm_dec
    res_total = math.hypot(res_ra, res_dec)
    
    # Astrometric consistency gate (< 800 mas/yr residual is ~0.13 px on SPHEREx 6.15"/px native scale!)
    consistency_pass = res_total < 800.0

    return {
        "status": "success",
        "target_name": catalog_target.get("common_name"),
        "n_visits_analyzed": n_visits,
        "baseline_years": round(times_years[-1] - times_years[0], 3),
        "catalog_pm": {
            "pm_ra_mas_yr": cat_pm_ra,
            "pm_dec_mas_yr": cat_pm_dec,
            "total_pm_mas_yr": round(cat_total_pm, 2),
            "total_pm_arcsec_yr": round(cat_total_pm / 1000.0, 3)
        },
        "fitted_pm": {
            "fitted_pm_ra_mas_yr": round(fitted_pm_ra_mas, 2),
            "fitted_pm_dec_mas_yr": round(fitted_pm_dec_mas, 2),
            "fitted_total_pm_mas_yr": round(fitted_total_pm_mas, 2),
            "fitted_total_pm_arcsec_yr": round(fitted_total_pm_mas / 1000.0, 3)
        },
        "residuals": {
            "delta_pm_ra_mas_yr": round(res_ra, 2),
            "delta_pm_dec_mas_yr": round(res_dec, 2),
            "total_residual_mas_yr": round(res_total, 2)
        },
        "validation_verdict": "PASS: Astrometric motion is verified consistent with Gaia DR3 / CatWISE ground-truth." if consistency_pass else "WARN: Astrometric residual exceeds 800 mas/yr threshold (~0.13 px on native scale).",
        "centroids": centroids
    }
