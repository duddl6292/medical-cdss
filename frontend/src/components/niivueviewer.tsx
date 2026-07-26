import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

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

  onOverlayOpacityChange?: (value: number) => void;
  onOverlayVisibleChange?: (value: boolean) => void;
};

type LocationData = {
  frac?: number[];
};

const DEFAULT_ZOOM = 1;

function NiivueViewer({
  originalUrl,
  maskUrl,
  overlayOpacity = 0.6,
  overlayVisible = true,
  viewerMode = "axial",
  onOverlayOpacityChange,
  onOverlayVisibleChange,
}: NiivueViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const niivueRef = useRef<Niivue | null>(null);

  const [zoom, setZoom] = useState(DEFAULT_ZOOM);
  const [sliceIndex, setSliceIndex] = useState(1);
  const [sliceCount, setSliceCount] = useState(1);

  /*
   * 현재 슬라이스를 중심으로
   * 하단에 최대 9개의 슬라이스 번호를 표시합니다.
   */
  const thumbnailSlices = useMemo(() => {
    if (sliceCount <= 1) {
      return [1];
    }

    const visibleCount = Math.min(9, sliceCount);
    const half = Math.floor(visibleCount / 2);

    let start = Math.max(1, sliceIndex - half);
    let end = Math.min(
      sliceCount,
      start + visibleCount - 1,
    );

    start = Math.max(
      1,
      end - visibleCount + 1,
    );

    return Array.from(
      { length: end - start + 1 },
      (_, index) => start + index,
    );
  }, [sliceCount, sliceIndex]);

  /*
   * NiiVue 생성 및 NIfTI 파일 로딩
   */
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

          // 멀티뷰에서 별도의 3D 렌더링 영역을 숨깁니다.
          multiplanarShowRender: 0,

          // 캔버스에 마우스가 올라간 경우에만 스크롤합니다.
          scrollRequiresFocus: true,
        });

        niivueRef.current = nv;

        await nv.attachToCanvas(canvasRef.current);

        /*
         * 2D 화면에서 이동과 확대·축소를 사용할 수 있도록 합니다.
         */
        nv.setSliceMM(true);

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

        const totalSlices = getSliceCount(
          nv,
          viewerMode,
        );

        const middleSlice = Math.max(
          1,
          Math.ceil(totalSlices / 2),
        );

        setSliceCount(totalSlices);
        setSliceIndex(middleSlice);

        moveToSlice(
          nv,
          viewerMode,
          middleSlice,
          totalSlices,
        );

        /*
         * NiiVue 내부에서 위치가 바뀐 경우
         * React의 Slice 값도 함께 변경합니다.
         */
        nv.onLocationChange = (
          location: unknown,
        ) => {
          const data = location as LocationData;

          const nextSlice =
            getSliceIndexFromLocation(
              data,
              viewerMode,
              totalSlices,
            );

          if (nextSlice !== null) {
            setSliceIndex(nextSlice);
          }
        };
      } catch (error) {
        console.error(
          "Niivue 영상 로딩 오류:",
          error,
        );
      }
    }

    initializeViewer();

    return () => {
      cancelled = true;

      if (niivueRef.current) {
        niivueRef.current.onLocationChange =
          () => {};
      }

      niivueRef.current = null;
    };
  }, [originalUrl, maskUrl]);

  /*
   * Axial, Coronal, Sagittal, Multi View 변경
   */
  useEffect(() => {
    const nv = niivueRef.current;

    if (!nv || nv.volumes.length === 0) {
      return;
    }

    setViewerSliceType(nv, viewerMode);

    const totalSlices = getSliceCount(
      nv,
      viewerMode,
    );

    const middleSlice = Math.max(
      1,
      Math.ceil(totalSlices / 2),
    );

    setSliceCount(totalSlices);
    setSliceIndex(middleSlice);

    moveToSlice(
      nv,
      viewerMode,
      middleSlice,
      totalSlices,
    );

    setZoom(DEFAULT_ZOOM);

    nv.setPan2Dxyzmm([
      0,
      0,
      0,
      DEFAULT_ZOOM,
    ]);
  }, [viewerMode]);

  /*
   * 오버레이 표시 여부와 투명도 반영
   */
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

  /*
   * 확대·축소
   */
  const handleZoomChange = (
    nextZoom: number,
  ) => {
    const nv = niivueRef.current;

    if (!nv) {
      return;
    }

    const safeZoom = Math.min(
      4,
      Math.max(0.5, nextZoom),
    );

    setZoom(safeZoom);

    nv.setPan2Dxyzmm([
      0,
      0,
      0,
      safeZoom,
    ]);
  };

  /*
   * 슬라이스 변경
   */
  const handleSliceChange = (
    nextSlice: number,
  ) => {
    const nv = niivueRef.current;

    if (
      !nv ||
      viewerMode === "multiplanar"
    ) {
      return;
    }

    const safeSlice = Math.min(
      sliceCount,
      Math.max(1, nextSlice),
    );

    setSliceIndex(safeSlice);

    moveToSlice(
      nv,
      viewerMode,
      safeSlice,
      sliceCount,
    );
  };

  /*
   * 화면 초기화
   */
  const handleReset = () => {
    const nv = niivueRef.current;

    if (!nv) {
      return;
    }

    const middleSlice = Math.max(
      1,
      Math.ceil(sliceCount / 2),
    );

    setZoom(DEFAULT_ZOOM);
    setSliceIndex(middleSlice);

    nv.setPan2Dxyzmm([
      0,
      0,
      0,
      DEFAULT_ZOOM,
    ]);

    moveToSlice(
      nv,
      viewerMode,
      middleSlice,
      sliceCount,
    );
  };

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      <div className="grid min-h-[560px] grid-cols-1 lg:grid-cols-[64px_minmax(0,1fr)_270px]">
        {/* 왼쪽 도구 영역 */}
        <aside className="flex flex-row items-center justify-center gap-2 border-b border-slate-200 bg-slate-50 p-3 lg:flex-col lg:border-b-0 lg:border-r">
          <button
            type="button"
            onClick={() =>
              handleZoomChange(zoom + 0.2)
            }
            title="확대"
            className="flex h-11 w-11 items-center justify-center rounded-lg border border-slate-300 bg-white text-xl font-bold text-slate-700 transition hover:border-blue-500 hover:text-blue-600"
          >
            +
          </button>

          <button
            type="button"
            onClick={() =>
              handleZoomChange(zoom - 0.2)
            }
            title="축소"
            className="flex h-11 w-11 items-center justify-center rounded-lg border border-slate-300 bg-white text-xl font-bold text-slate-700 transition hover:border-blue-500 hover:text-blue-600"
          >
            −
          </button>

          <button
            type="button"
            onClick={handleReset}
            title="화면 초기화"
            className="flex h-11 w-11 items-center justify-center rounded-lg border border-slate-300 bg-white text-lg font-semibold text-slate-700 transition hover:border-blue-500 hover:text-blue-600"
          >
            ↺
          </button>
        </aside>

        {/* 영상 영역 */}
        <section className="flex min-w-0 flex-col bg-black">
          <div className="relative min-h-[450px] flex-1">
            <canvas
              ref={canvasRef}
              className="absolute inset-0 h-full w-full"
            />

            <div className="pointer-events-none absolute left-4 top-4 rounded bg-black/60 px-3 py-2 text-sm font-semibold text-white">
              <p>
                {getViewerLabel(viewerMode)}
              </p>

              {viewerMode !==
                "multiplanar" && (
                <p className="mt-1 text-xs font-normal text-slate-200">
                  {sliceIndex} / {sliceCount}
                </p>
              )}
            </div>
          </div>

          {/* 하단 슬라이스 선택 바 */}
          {viewerMode !== "multiplanar" && (
            <div className="border-t border-slate-700 bg-slate-950 px-4 py-3">
              <div className="flex gap-2 overflow-x-auto pb-1">
                {thumbnailSlices.map(
                  (sliceNumber) => {
                    const isSelected =
                      sliceNumber === sliceIndex;

                    return (
                      <button
                        key={sliceNumber}
                        type="button"
                        onClick={() =>
                          handleSliceChange(
                            sliceNumber,
                          )
                        }
                        className={`flex h-[72px] min-w-[72px] flex-col items-center justify-center rounded-lg border text-xs font-semibold transition ${
                          isSelected
                            ? "border-blue-400 bg-blue-500/20 text-blue-200"
                            : "border-slate-600 bg-slate-900 text-slate-300 hover:border-slate-400"
                        }`}
                      >
                        <span className="text-xl">
                          ◉
                        </span>

                        <span className="mt-1 text-base">
                          {sliceNumber}
                        </span>
                      </button>
                    );
                  },
                )}
              </div>
            </div>
          )}
        </section>

        {/* 오른쪽 뷰어 컨트롤 */}
        <aside className="border-t border-slate-200 bg-white p-6 lg:border-l lg:border-t-0">
          <h3 className="mb-6 text-xl font-bold text-slate-900">
            뷰어 컨트롤
          </h3>

          {/* Zoom */}
          <div className="mb-7">
            <div className="mb-2 flex items-center justify-between">
              <label
                htmlFor="viewer-zoom"
                className="text-sm font-semibold text-slate-700"
              >
                Zoom
              </label>

              <span className="text-sm font-medium text-slate-500">
                {zoom.toFixed(1)}
              </span>
            </div>

            <input
              id="viewer-zoom"
              type="range"
              min="0.5"
              max="4"
              step="0.1"
              value={zoom}
              onChange={(event) =>
                handleZoomChange(
                  Number(event.target.value),
                )
              }
              className="w-full accent-blue-600"
            />
          </div>

          {/* 병변 오버레이 */}
          <div className="mb-7 border-t border-slate-100 pt-6">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-bold text-slate-800">
                  병변 오버레이
                </p>

                <p className="mt-1 text-xs leading-5 text-slate-400">
                  AI가 탐지한 병변 마스크를
                  표시합니다.
                </p>
              </div>

              <button
                type="button"
                onClick={() =>
                  onOverlayVisibleChange?.(
                    !overlayVisible,
                  )
                }
                aria-label="병변 오버레이 표시 전환"
                className={`relative h-7 w-12 shrink-0 rounded-full transition ${
                  overlayVisible
                    ? "bg-blue-600"
                    : "bg-slate-300"
                }`}
              >
                <span
                  className={`absolute top-1 h-5 w-5 rounded-full bg-white shadow-sm transition-all ${
                    overlayVisible
                      ? "left-6"
                      : "left-1"
                  }`}
                />
              </button>
            </div>

            <div className="mb-2 flex items-center justify-between">
              <label
                htmlFor="viewer-opacity"
                className="text-sm font-semibold text-slate-700"
              >
                Opacity
              </label>

              <span className="text-sm font-medium text-blue-600">
                {Math.round(
                  overlayOpacity * 100,
                )}
                %
              </span>
            </div>

            <input
              id="viewer-opacity"
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={overlayOpacity}
              disabled={!overlayVisible}
              onChange={(event) =>
                onOverlayOpacityChange?.(
                  Number(event.target.value),
                )
              }
              className="w-full accent-blue-600 disabled:cursor-not-allowed disabled:opacity-40"
            />
          </div>

          {/* Slice */}
          {viewerMode !== "multiplanar" && (
            <div className="mb-7 border-t border-slate-100 pt-6">
              <div className="mb-2 flex items-center justify-between">
                <label
                  htmlFor="viewer-slice"
                  className="text-sm font-semibold text-slate-700"
                >
                  Slice
                </label>

                <span className="text-sm font-medium text-slate-500">
                  {sliceIndex} / {sliceCount}
                </span>
              </div>

              <input
                id="viewer-slice"
                type="range"
                min="1"
                max={sliceCount}
                step="1"
                value={sliceIndex}
                onChange={(event) =>
                  handleSliceChange(
                    Number(event.target.value),
                  )
                }
                className="w-full accent-blue-600"
              />

              <div className="mt-2 flex justify-between text-xs text-slate-400">
                <span>1</span>
                <span>{sliceCount}</span>
              </div>
            </div>
          )}

          {/* 확대·축소·초기화 */}
          <div className="grid grid-cols-2 gap-2 border-t border-slate-100 pt-6">
            <button
              type="button"
              onClick={() =>
                handleZoomChange(zoom - 0.2)
              }
              className="rounded-lg border border-slate-300 px-3 py-3 text-sm font-semibold text-slate-600 transition hover:border-blue-400 hover:bg-blue-50 hover:text-blue-600"
            >
              축소
            </button>

            <button
              type="button"
              onClick={() =>
                handleZoomChange(zoom + 0.2)
              }
              className="rounded-lg border border-slate-300 px-3 py-3 text-sm font-semibold text-slate-600 transition hover:border-blue-400 hover:bg-blue-50 hover:text-blue-600"
            >
              확대
            </button>

            <button
              type="button"
              onClick={handleReset}
              className="col-span-2 rounded-lg bg-slate-800 px-3 py-3 text-sm font-semibold text-white transition hover:bg-slate-700"
            >
              화면 초기화
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
}

function setViewerSliceType(
  nv: Niivue,
  viewerMode: ViewerMode,
) {
  switch (viewerMode) {
    case "coronal":
      nv.setSliceType(
        SLICE_TYPE.CORONAL,
      );
      break;

    case "sagittal":
      nv.setSliceType(
        SLICE_TYPE.SAGITTAL,
      );
      break;

    case "multiplanar":
      nv.opts.multiplanarShowRender = 0;

      nv.setSliceType(
        SLICE_TYPE.MULTIPLANAR,
      );
      break;

    case "axial":
    default:
      nv.setSliceType(
        SLICE_TYPE.AXIAL,
      );
  }
}

function getSliceCount(
  nv: Niivue,
  viewerMode: ViewerMode,
) {
  const volume = nv.volumes[0];

  if (!volume?.dims) {
    return 1;
  }

  switch (viewerMode) {
    case "sagittal":
      return Math.max(
        1,
        volume.dims[1] ?? 1,
      );

    case "coronal":
      return Math.max(
        1,
        volume.dims[2] ?? 1,
      );

    case "axial":
    case "multiplanar":
    default:
      return Math.max(
        1,
        volume.dims[3] ?? 1,
      );
  }
}

function moveToSlice(
  nv: Niivue,
  viewerMode: ViewerMode,
  sliceIndex: number,
  sliceCount: number,
) {
  if (sliceCount <= 1) {
    return;
  }

  const normalizedPosition =
    (sliceIndex - 1) /
    (sliceCount - 1);

  const scene = nv.scene as {
    crosshairPos: number[];
  };

  const currentPosition = [
    scene.crosshairPos?.[0] ?? 0.5,
    scene.crosshairPos?.[1] ?? 0.5,
    scene.crosshairPos?.[2] ?? 0.5,
  ];

  switch (viewerMode) {
    case "sagittal":
      currentPosition[0] =
        normalizedPosition;
      break;

    case "coronal":
      currentPosition[1] =
        normalizedPosition;
      break;

    case "axial":
    default:
      currentPosition[2] =
        normalizedPosition;
  }

  scene.crosshairPos = currentPosition;

  nv.drawScene();
}

function getSliceIndexFromLocation(
  location: LocationData,
  viewerMode: ViewerMode,
  sliceCount: number,
) {
  if (
    !location.frac ||
    location.frac.length < 3 ||
    sliceCount <= 1
  ) {
    return null;
  }

  let fraction =
    location.frac[2];

  if (viewerMode === "sagittal") {
    fraction = location.frac[0];
  }

  if (viewerMode === "coronal") {
    fraction = location.frac[1];
  }

  const nextSlice =
    Math.round(
      fraction * (sliceCount - 1),
    ) + 1;

  return Math.min(
    sliceCount,
    Math.max(1, nextSlice),
  );
}

function getViewerLabel(
  viewerMode: ViewerMode,
) {
  switch (viewerMode) {
    case "coronal":
      return "Coronal";

    case "sagittal":
      return "Sagittal";

    case "multiplanar":
      return "Multi View";

    case "axial":
    default:
      return "Axial";
  }
}

export default NiivueViewer;