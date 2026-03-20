import { useEffect } from 'react'
import { useScenarioEditorStore, FileTreeNode } from '../store/scenarioEditor'

// Icons for different node types
const FolderIcon = ({ open }: { open?: boolean }) => (
  <svg
    className={`w-4 h-4 ${open ? 'text-yellow-400' : 'text-yellow-500'}`}
    fill="currentColor"
    viewBox="0 0 20 20"
  >
    {open ? (
      <path
        fillRule="evenodd"
        d="M2 6a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1H8a3 3 0 00-3 3v1.5a1.5 1.5 0 01-3 0V6z"
        clipRule="evenodd"
      />
    ) : (
      <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
    )}
  </svg>
)

const RepoIcon = () => (
  <svg className="w-4 h-4 text-purple-400" fill="currentColor" viewBox="0 0 20 20">
    <path
      fillRule="evenodd"
      d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 110 2h-3a1 1 0 01-1-1v-2a1 1 0 00-1-1H9a1 1 0 00-1 1v2a1 1 0 01-1 1H4a1 1 0 110-2V4zm3 1h2v2H7V5zm2 4H7v2h2V9zm2-4h2v2h-2V5zm2 4h-2v2h2V9z"
      clipRule="evenodd"
    />
  </svg>
)

const FileIcon = () => (
  <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
    <path
      fillRule="evenodd"
      d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z"
      clipRule="evenodd"
    />
  </svg>
)

const ChevronIcon = ({ expanded }: { expanded: boolean }) => (
  <svg
    className={`w-4 h-4 text-gray-500 transition-transform ${expanded ? 'rotate-90' : ''}`}
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
  >
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
  </svg>
)

interface TreeNodeProps {
  node: FileTreeNode
  depth: number
  expanded: boolean
  currentFileId?: string
  onToggle: (nodeId: string) => void
  onSelect: (scenarioId: string) => void
}

function TreeNode({ node, depth, expanded, currentFileId, onToggle, onSelect }: TreeNodeProps) {
  const isFile = node.type === 'file'
  const hasChildren = node.children && node.children.length > 0
  const isSelected = node.scenarioId && `scenario-${currentFileId}` === node.id
  const paddingLeft = 12 + depth * 16

  const handleClick = () => {
    if (isFile && node.scenarioId) {
      onSelect(node.scenarioId)
    } else if (hasChildren) {
      onToggle(node.id)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      handleClick()
    }
  }

  return (
    <div>
      <div
        className={`
          flex items-center gap-1.5 py-1.5 px-2 cursor-pointer select-none
          hover:bg-gray-700/50 transition-colors
          ${isSelected ? 'bg-blue-600/30 text-blue-300' : 'text-gray-300'}
        `}
        style={{ paddingLeft }}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        role="treeitem"
        tabIndex={0}
        aria-expanded={hasChildren ? expanded : undefined}
        aria-selected={isSelected || undefined}
      >
        {/* Expand/collapse chevron */}
        {hasChildren ? (
          <span className="flex-shrink-0">
            <ChevronIcon expanded={expanded} />
          </span>
        ) : (
          <span className="w-4" />
        )}

        {/* Icon based on type */}
        <span className="flex-shrink-0">
          {node.type === 'repo' ? (
            <RepoIcon />
          ) : node.type === 'folder' ? (
            <FolderIcon open={expanded} />
          ) : (
            <FileIcon />
          )}
        </span>

        {/* Name */}
        <span className="truncate text-sm" title={node.name}>
          {node.name}
        </span>

        {/* Badge for children count */}
        {hasChildren && !expanded && (
          <span className="ml-auto text-xs text-gray-500 bg-gray-700 px-1.5 py-0.5 rounded">
            {node.children!.length}
          </span>
        )}
      </div>

      {/* Children */}
      {hasChildren && expanded && (
        <div role="group">
          {node.children!.map((child) => (
            <TreeNodeWrapper
              key={child.id}
              node={child}
              depth={depth + 1}
              currentFileId={currentFileId}
              onToggle={onToggle}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// Wrapper to connect to store for expanded state
function TreeNodeWrapper({
  node,
  depth,
  currentFileId,
  onToggle,
  onSelect,
}: Omit<TreeNodeProps, 'expanded'>) {
  const expandedNodes = useScenarioEditorStore((state) => state.expandedNodes)
  const expanded = expandedNodes.has(node.id)

  return (
    <TreeNode
      node={node}
      depth={depth}
      expanded={expanded}
      currentFileId={currentFileId}
      onToggle={onToggle}
      onSelect={onSelect}
    />
  )
}

interface ScenarioTreeProps {
  onSelectScenario?: (scenarioId: string) => void
}

export default function ScenarioTree({ onSelectScenario }: ScenarioTreeProps) {
  const {
    fileTree,
    loadingTree,
    currentFile,
    loadFileTree,
    loadFile,
    toggleNode,
  } = useScenarioEditorStore()

  useEffect(() => {
    loadFileTree()
  }, [loadFileTree])

  const handleSelect = (scenarioId: string) => {
    loadFile(scenarioId)
    onSelectScenario?.(scenarioId)
  }

  if (loadingTree) {
    return (
      <div className="p-4 space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="flex items-center gap-2 animate-pulse">
            <div className="w-4 h-4 bg-gray-700 rounded" />
            <div className="w-4 h-4 bg-gray-700 rounded" />
            <div className="h-4 bg-gray-700 rounded flex-1" />
          </div>
        ))}
      </div>
    )
  }

  if (fileTree.length === 0) {
    return (
      <div className="p-4 text-center">
        <svg
          className="w-12 h-12 mx-auto text-gray-600 mb-3"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
          />
        </svg>
        <p className="text-gray-500 text-sm">No scenarios found</p>
        <p className="text-gray-600 text-xs mt-1">Add and sync a repository first</p>
      </div>
    )
  }

  return (
    <div className="py-2" role="tree" aria-label="Scenario files">
      {fileTree.map((node) => (
        <TreeNodeWrapper
          key={node.id}
          node={node}
          depth={0}
          currentFileId={currentFile?.id}
          onToggle={toggleNode}
          onSelect={handleSelect}
        />
      ))}
    </div>
  )
}
