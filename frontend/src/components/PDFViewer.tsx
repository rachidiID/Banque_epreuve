import { useState, useEffect } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import { FaChevronLeft, FaChevronRight, FaExpand, FaCompress, FaDownload } from 'react-icons/fa'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'

// Configuration du worker PDF.js
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`

interface PDFViewerProps {
  url: string
  onDownload?: () => void
  filename?: string
}

const PDFViewer = ({ url, onDownload, filename = 'document.pdf' }: PDFViewerProps) => {
  const [numPages, setNumPages] = useState<number>(0)
  const [pageNumber, setPageNumber] = useState<number>(1)
  const [scale, setScale] = useState<number>(1.0)
  const [isFullscreen, setIsFullscreen] = useState(false)

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
  }

  const changePage = (offset: number) => {
    setPageNumber((prevPageNumber) => Math.max(1, Math.min(prevPageNumber + offset, numPages)))
  }

  const previousPage = () => changePage(-1)
  const nextPage = () => changePage(1)

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen()
      setIsFullscreen(true)
    } else {
      document.exitFullscreen()
      setIsFullscreen(false)
    }
  }

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }
    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange)
  }, [])

  return (
    <div className="bg-gray-100 rounded-lg p-4 space-y-4">
      {/* Barre d'outils */}
      <div className="bg-white rounded-lg shadow p-3 flex items-center justify-between flex-wrap gap-2">
        {/* Navigation */}
        <div className="flex items-center gap-2">
          <button
            onClick={previousPage}
            disabled={pageNumber <= 1}
            className="p-2 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Page précédente"
          >
            <FaChevronLeft />
          </button>
          <span className="text-sm font-medium px-2">
            {pageNumber} / {numPages || '...'}
          </span>
          <button
            onClick={nextPage}
            disabled={pageNumber >= numPages}
            className="p-2 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Page suivante"
          >
            <FaChevronRight />
          </button>
        </div>

        {/* Zoom */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setScale((s) => Math.max(0.5, s - 0.1))}
            className="px-3 py-1 rounded hover:bg-gray-100 text-sm font-medium transition-colors"
          >
            -
          </button>
          <span className="text-sm font-medium px-2">{Math.round(scale * 100)}%</span>
          <button
            onClick={() => setScale((s) => Math.min(2.0, s + 0.1))}
            className="px-3 py-1 rounded hover:bg-gray-100 text-sm font-medium transition-colors"
          >
            +
          </button>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={toggleFullscreen}
            className="p-2 rounded hover:bg-gray-100 transition-colors"
            title={isFullscreen ? 'Quitter le plein écran' : 'Plein écran'}
          >
            {isFullscreen ? <FaCompress /> : <FaExpand />}
          </button>
          {onDownload && (
            <button
              onClick={onDownload}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 transition-colors text-sm font-medium"
              title="Télécharger"
            >
              <FaDownload />
              <span className="hidden sm:inline">Télécharger</span>
            </button>
          )}
        </div>
      </div>

      {/* Viewer PDF */}
      <div className="bg-white rounded-lg shadow-lg overflow-auto" style={{ maxHeight: '70vh' }}>
        <div className="flex justify-center p-4">
          <Document
            file={url}
            onLoadSuccess={onDocumentLoadSuccess}
            loading={
              <div className="flex flex-col items-center justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent"></div>
                <p className="mt-4 text-gray-600">Chargement du PDF...</p>
              </div>
            }
            error={
              <div className="text-center py-12">
                <p className="text-red-600 font-medium mb-2">Erreur de chargement du PDF</p>
                <p className="text-sm text-gray-600">Impossible de charger le document</p>
              </div>
            }
          >
            <Page
              pageNumber={pageNumber}
              scale={scale}
              renderTextLayer={true}
              renderAnnotationLayer={true}
              className="shadow-lg"
            />
          </Document>
        </div>
      </div>

      {/* Info bas de page */}
      <div className="text-center text-sm text-gray-600">
        <p>Utilisez les touches fléchées ← → pour naviguer entre les pages</p>
      </div>
    </div>
  )
}

export default PDFViewer
