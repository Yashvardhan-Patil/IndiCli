import { useEffect, useRef, useState } from "react";
import useStore from "@/store/useStore";

const CESIUM_TOKEN = import.meta.env.VITE_CESIUM_TOKEN;

const CAMERA_TARGETS = [
  { label: "India", lon: 80.0, lat: 22.0, height: 3_500_000, pitch: -55 },
  { label: "Delhi", lon: 77.209, lat: 28.6139, height: 1_200, pitch: -25 },
  { label: "Mumbai", lon: 72.8777, lat: 19.076, height: 1_200, pitch: -25 },
  { label: "Bengaluru", lon: 77.5946, lat: 12.9716, height: 1_200, pitch: -25 },
];

// Color scale helpers
function rainfallColor(value) {
  if (value === null || value === undefined) return null;
  if (value <= 0)   return { r: 240, g: 240, b: 240, a: 0.1 };
  if (value <= 5)   return { r: 173, g: 216, b: 230, a: 0.6 };
  if (value <= 20)  return { r: 100, g: 149, b: 237, a: 0.7 };
  if (value <= 50)  return { r: 0,   g: 0,   b: 255, a: 0.75 };
  if (value <= 100) return { r: 0,   g: 0,   b: 180, a: 0.8 };
  return               { r: 75,  g: 0,   b: 130, a: 0.85 };
}

function tempColor(value, isMax) {
  if (value === null || value === undefined) return null;
  const v = value;
  if (isMax) {
    if (v < 20) return { r: 135, g: 206, b: 250, a: 0.7 };
    if (v < 30) return { r: 144, g: 238, b: 144, a: 0.7 };
    if (v < 35) return { r: 255, g: 255, b: 0,   a: 0.75 };
    if (v < 40) return { r: 255, g: 165, b: 0,   a: 0.8 };
    return              { r: 220, g: 20,  b: 20,  a: 0.85 };
  } else {
    if (v < 5)  return { r: 173, g: 216, b: 230, a: 0.8 };
    if (v < 15) return { r: 100, g: 149, b: 237, a: 0.7 };
    if (v < 20) return { r: 144, g: 238, b: 144, a: 0.7 };
    return              { r: 255, g: 200, b: 100, a: 0.65 };
  }
}

function getColor(variable, value) {
  if (variable === "rainfall") return rainfallColor(value);
  if (variable === "max_temp") return tempColor(value, true);
  if (variable === "min_temp") return tempColor(value, false);
  return null;
}

export default function CesiumGlobe({ gridData }) {
  const containerRef  = useRef(null);
  const viewerRef     = useRef(null);
  const entitiesRef   = useRef([]);
  const [buildingsReady, setBuildingsReady] = useState(false);
  const { selectedVariable, setSelectedLocation } = useStore();

  const flyToTarget = async (target) => {
    const viewer = viewerRef.current;
    if (!viewer) return;
    const Cesium = await import("cesium");

    viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(target.lon, target.lat, target.height),
      orientation: {
        heading: Cesium.Math.toRadians(0),
        pitch:   Cesium.Math.toRadians(target.pitch),
        roll:    0,
      },
      duration: 1.0,
    });
  };

  // Initialize Cesium viewer
  useEffect(() => {
    let viewer = null;

    async function init() {
      if (!containerRef.current || viewerRef.current) return;

      try {
        const Cesium = await import("cesium");
        await import("cesium/Build/Cesium/Widgets/widgets.css");

        Cesium.Ion.defaultAccessToken = CESIUM_TOKEN || "";

        viewer = new Cesium.Viewer(containerRef.current, {
          imageryProvider: new Cesium.OpenStreetMapImageryProvider({
            url: "https://tile.openstreetmap.org/",
          }),
          terrainProvider: CESIUM_TOKEN
            ? await Cesium.createWorldTerrainAsync()
            : new Cesium.EllipsoidTerrainProvider(),
          baseLayerPicker:      false,
          geocoder:             false,
          homeButton:           false,
          sceneModePicker:      false,
          navigationHelpButton: false,
          animation:            false,
          timeline:             false,
          fullscreenButton:     false,
          infoBox:              false,
          selectionIndicator:   false,
        });
        viewer.scene.globe.depthTestAgainstTerrain = false;

        // Load 3D buildings if token is present
        if (CESIUM_TOKEN) {
          try {
            const buildingsTileset = await Cesium.createOsmBuildingsAsync();
            viewer.scene.primitives.add(buildingsTileset);
            setBuildingsReady(true);
          } catch (err) {
            console.error("Error loading 3D OSM buildings:", err);
          }
        }

        // Fly to India
        viewer.camera.flyTo({
          destination: Cesium.Cartesian3.fromDegrees(
            CAMERA_TARGETS[0].lon,
            CAMERA_TARGETS[0].lat,
            CAMERA_TARGETS[0].height
          ),
          orientation: {
            heading: Cesium.Math.toRadians(0),
            pitch:   Cesium.Math.toRadians(CAMERA_TARGETS[0].pitch),
            roll:    0,
          },
          duration: 1.5,
        });

        // Click handler
        const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
        handler.setInputAction((click) => {
          const ray      = viewer.camera.getPickRay(click.position);
          const cartesian= viewer.scene.globe.pick(ray, viewer.scene);
          if (cartesian) {
            const carto = Cesium.Cartographic.fromCartesian(cartesian);
            const lat   = Cesium.Math.toDegrees(carto.latitude);
            const lon   = Cesium.Math.toDegrees(carto.longitude);
            setSelectedLocation(parseFloat(lat.toFixed(2)), parseFloat(lon.toFixed(2)));
          }
        }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

        viewerRef.current = viewer;
      } catch (e) {
        console.error("Cesium init error:", e);
      }
    }

    init();

    return () => {
      if (viewerRef.current && !viewerRef.current.isDestroyed()) {
        viewerRef.current.destroy();
        viewerRef.current = null;
      }
    };
  }, []);

  // Update grid data entities
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || !gridData?.length) return;

    async function updateEntities() {
      try {
        const Cesium = await import("cesium");

        // Remove old entities
        entitiesRef.current.forEach((e) => viewer.entities.remove(e));
        entitiesRef.current = [];

        // Add new colored rectangles for each grid point
        const HALF = 0.125; // half cell size for 0.25-deg grid
        for (const pt of gridData) {
          const color = getColor(selectedVariable, pt.value ?? pt[selectedVariable]);
          if (!color) continue;

          const entity = viewer.entities.add({
            rectangle: {
              coordinates: Cesium.Rectangle.fromDegrees(
                pt.longitude - HALF, pt.latitude - HALF,
                pt.longitude + HALF, pt.latitude + HALF
              ),
              material: new Cesium.Color(
                color.r / 255, color.g / 255, color.b / 255, color.a
              ),
              height: 1500,
              outline: true,
              outlineColor: Cesium.Color.WHITE.withAlpha(0.18),
            },
          });
          entitiesRef.current.push(entity);
        }
        viewer.scene.requestRender();
      } catch (e) {
        console.error("Entity update error:", e);
      }
    }

    updateEntities();
  }, [gridData, selectedVariable]);

  return (
    <div className="cesium-container w-full h-full">
      <div ref={containerRef} style={{ width: "100%", height: "100%" }} />
      <div className="absolute top-3 right-3 flex flex-wrap justify-end gap-2 max-w-sm">
        {CAMERA_TARGETS.map((target) => (
          <button
            key={target.label}
            type="button"
            onClick={() => flyToTarget(target)}
            className="px-2.5 py-1.5 rounded-md bg-surface-card/90 border border-surface-border text-xs text-slate-200 hover:bg-surface-border"
          >
            {target.label}
          </button>
        ))}
      </div>
      {CESIUM_TOKEN && !buildingsReady && (
        <div className="absolute bottom-3 left-3 bg-surface-card/90 text-slate-300 text-xs px-3 py-1.5 rounded-lg border border-surface-border">
          Loading 3D buildings...
        </div>
      )}
      {!CESIUM_TOKEN && (
        <div className="absolute top-3 left-3 bg-amber-900/80 text-amber-200 text-xs px-3 py-1.5 rounded-lg border border-amber-700">
          ⚠️ Set VITE_CESIUM_TOKEN in .env for terrain rendering
        </div>
      )}
    </div>
  );
}
