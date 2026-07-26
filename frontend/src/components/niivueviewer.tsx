import { useEffect, useRef } from "react";
import {
  Niivue,
  SLICE_TYPE,
} from "@niivue/niivue";

export type ViewerMode =
  | "axial"
  | "coronal"
  | "sagittal"
  | "multiplanar";

type NiivueViewerProps = {
  originalUrl: string;
  maskUrl?: string;
  overlayOpacity?: number;
  overlayVisible?: boolean;
  viewerMode?: ViewerMode;
};

function NiivueViewer({
  originalUrl,
  maskUrl,
  overlayOpacity = 0.6,
  overlayVisible = true,
  viewerMode = "axial",
}: NiivueViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const niivueRef = useRef<Niivue | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function initializeViewer() {
      if (!canvasRef.current || !originalUrl) {
        return;
      }

      try {
        const nv = new Niivue({
          isColorbar: false,
          backColor: [0, 0, 0, 1],
        });

        niivueRef.current = nv;

        await nv.attachToCanvas(canvasRef.current);

        const volumes: {
          url: string;
          name: string;
          colormap: string;
          opacity: number;
        }[] = [
          {
            url: originalUrl,
            name: "original.nii.gz",
            colormap: "gray",
            opacity: 1,
          },
        ];

        if (maskUrl) {
          volumes.push({
            url: maskUrl,
            name: "mask.nii.gz",
            colormap: "red",
            opacity: overlayVisible
              ? overlayOpacity
              : 0,
          });
        }

        await nv.loadVolumes(volumes);

        if (cancelled) {
          return;
        }

        setViewerSliceType(nv, viewerMode);
      } catch (error) {
        console.error("Niivue 영상 로딩 오류:", error);
      }
    }

    initializeViewer();

    return () => {
      cancelled = true;
      niivueRef.current = null;
    };
  }, [originalUrl, maskUrl]);

  useEffect(() => {
    const nv = niivueRef.current;

    if (!nv) {
      return;
    }

    setViewerSliceType(nv, viewerMode);
  }, [viewerMode]);

  useEffect(() => {
    const nv = niivueRef.current;

    if (!nv || nv.volumes.length < 2) {
      return;
    }

    nv.setOpacity(
      1,
      overlayVisible ? overlayOpacity : 0,
    );

    nv.updateGLVolume();
  }, [overlayOpacity, overlayVisible]);

  return (
    <div className="h-[560px] w-full overflow-hidden rounded-xl bg-black">
      <canvas
        ref={canvasRef}
        className="h-full w-full"
      />
    </div>
  );
}

function setViewerSliceType(
  nv: Niivue,
  viewerMode: ViewerMode,
) {
  switch (viewerMode) {
    case "coronal":
      nv.setSliceType(SLICE_TYPE.CORONAL);
      break;

    case "sagittal":
      nv.setSliceType(SLICE_TYPE.SAGITTAL);
      break;

    case "multiplanar":
      nv.setSliceType(SLICE_TYPE.MULTIPLANAR);
      break;

    case "axial":
    default:
      nv.setSliceType(SLICE_TYPE.AXIAL);
  }
}

export default NiivueViewer;