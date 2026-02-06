import { useState, useMemo, useRef, useEffect } from "react";
import { Folder, ChevronRight, Check, Search, X, FolderTree, RefreshCw } from "lucide-react";

interface FolderSelectorProps {
  folders: string[];
  selectedFolders: string[];
  onSelectionChange: (folders: string[]) => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

interface FolderNode {
  name: string;
  path: string;
  children: Map<string, FolderNode>;
}

function buildFolderTree(folders: string[]): FolderNode {
  const root: FolderNode = { name: "", path: "", children: new Map() };

  for (const folder of folders) {
    const parts = folder.split("/");
    let current = root;
    let pathSoFar = "";

    for (const part of parts) {
      pathSoFar = pathSoFar ? `${pathSoFar}/${part}` : part;
      if (!current.children.has(part)) {
        current.children.set(part, {
          name: part,
          path: pathSoFar,
          children: new Map(),
        });
      }
      current = current.children.get(part)!;
    }
  }

  return root;
}

function FolderTreeNode({
  node,
  level,
  selectedFolders,
  onToggle,
  expandedPaths,
  onToggleExpand,
  searchTerm,
}: {
  node: FolderNode;
  level: number;
  selectedFolders: string[];
  onToggle: (path: string) => void;
  expandedPaths: Set<string>;
  onToggleExpand: (path: string) => void;
  searchTerm: string;
}) {
  const hasChildren = node.children.size > 0;
  const isExpanded = expandedPaths.has(node.path);
  const isSelected = selectedFolders.includes(node.path);

  // Check if any children match search
  const matchesSearch = searchTerm === "" ||
    node.name.toLowerCase().includes(searchTerm.toLowerCase());

  const childrenArray = Array.from(node.children.values());
  const hasMatchingChildren = searchTerm !== "" && childrenArray.some(
    child => child.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    Array.from(child.children.values()).some(c =>
      c.name.toLowerCase().includes(searchTerm.toLowerCase())
    )
  );

  if (!matchesSearch && !hasMatchingChildren && searchTerm !== "") {
    return null;
  }

  return (
    <div>
      <div
        className={`group flex items-center gap-1 py-1.5 px-2 rounded-lg cursor-pointer transition-all duration-150 ${
          isSelected
            ? "bg-obsidian-100 dark:bg-obsidian-900/50"
            : "hover:bg-[rgb(var(--muted))]"
        }`}
        style={{ paddingLeft: `${level * 12 + 8}px` }}
      >
        {/* Expand/collapse button */}
        {hasChildren ? (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onToggleExpand(node.path);
            }}
            className="p-0.5 rounded hover:bg-[rgb(var(--border))] transition-colors"
          >
            <ChevronRight
              className={`h-3.5 w-3.5 text-[rgb(var(--muted-foreground))] transition-transform duration-150 ${
                isExpanded ? "rotate-90" : ""
              }`}
            />
          </button>
        ) : (
          <span className="w-4.5" />
        )}

        {/* Folder icon and name */}
        <button
          type="button"
          onClick={() => onToggle(node.path)}
          className="flex items-center gap-2 flex-1 min-w-0"
        >
          <Folder
            className={`h-4 w-4 flex-shrink-0 ${
              isSelected
                ? "text-obsidian-600 dark:text-obsidian-400"
                : "text-[rgb(var(--muted-foreground))]"
            }`}
          />
          <span
            className={`text-sm truncate ${
              isSelected
                ? "text-obsidian-700 dark:text-obsidian-300 font-medium"
                : "text-[rgb(var(--foreground))]"
            }`}
          >
            {node.name}
          </span>
        </button>

        {/* Selection indicator */}
        {isSelected && (
          <Check className="h-4 w-4 text-obsidian-600 dark:text-obsidian-400 flex-shrink-0" />
        )}
      </div>

      {/* Children */}
      {hasChildren && (isExpanded || searchTerm !== "") && (
        <div>
          {childrenArray.map((child) => (
            <FolderTreeNode
              key={child.path}
              node={child}
              level={level + 1}
              selectedFolders={selectedFolders}
              onToggle={onToggle}
              expandedPaths={expandedPaths}
              onToggleExpand={onToggleExpand}
              searchTerm={searchTerm}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function FolderSelector({
  folders,
  selectedFolders,
  onSelectionChange,
  onRefresh,
  isRefreshing = false,
}: FolderSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set());
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Build tree structure
  const folderTree = useMemo(() => buildFolderTree(folders), [folders]);

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Focus search when opening
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Auto-expand when searching
  useEffect(() => {
    if (searchTerm) {
      const allPaths = new Set<string>();
      folders.forEach(f => {
        const parts = f.split("/");
        let path = "";
        parts.forEach(p => {
          path = path ? `${path}/${p}` : p;
          allPaths.add(path);
        });
      });
      setExpandedPaths(allPaths);
    }
  }, [searchTerm, folders]);

  const toggleFolder = (path: string) => {
    if (selectedFolders.includes(path)) {
      onSelectionChange(selectedFolders.filter((f) => f !== path));
    } else {
      onSelectionChange([...selectedFolders, path]);
    }
  };

  const toggleExpand = (path: string) => {
    const newExpanded = new Set(expandedPaths);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedPaths(newExpanded);
  };

  const clearAll = () => {
    onSelectionChange([]);
    setSearchTerm("");
  };

  if (folders.length === 0) return null;

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 px-3 py-2 rounded-xl border transition-all duration-200 ${
          selectedFolders.length > 0
            ? "bg-obsidian-50 dark:bg-obsidian-900/30 border-obsidian-200 dark:border-obsidian-800"
            : "bg-[rgb(var(--muted))] border-[rgb(var(--border))] hover:border-obsidian-300 dark:hover:border-obsidian-700"
        }`}
      >
        <FolderTree className={`h-4 w-4 ${
          selectedFolders.length > 0
            ? "text-obsidian-600 dark:text-obsidian-400"
            : "text-[rgb(var(--muted-foreground))]"
        }`} />
        <span className={`text-sm ${
          selectedFolders.length > 0
            ? "text-obsidian-700 dark:text-obsidian-300 font-medium"
            : "text-[rgb(var(--muted-foreground))]"
        }`}>
          {selectedFolders.length === 0
            ? "All folders"
            : selectedFolders.length === 1
            ? selectedFolders[0].split("/").pop()
            : `${selectedFolders.length} folders`}
        </span>
        {selectedFolders.length > 0 && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              clearAll();
            }}
            className="p-0.5 rounded hover:bg-obsidian-200 dark:hover:bg-obsidian-800 transition-colors"
          >
            <X className="h-3.5 w-3.5 text-obsidian-500" />
          </button>
        )}
        <ChevronRight
          className={`h-4 w-4 text-[rgb(var(--muted-foreground))] transition-transform duration-200 ${
            isOpen ? "rotate-90" : ""
          }`}
        />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-72 max-h-80 bg-[rgb(var(--card))] border border-[rgb(var(--border))] rounded-xl shadow-xl z-50 overflow-hidden animate-fade-in">
          {/* Search */}
          <div className="p-2 border-b border-[rgb(var(--border))]">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[rgb(var(--muted-foreground))]" />
              <input
                ref={inputRef}
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search folders..."
                className="w-full pl-8 pr-3 py-2 text-sm rounded-lg bg-[rgb(var(--muted))] border-none text-[rgb(var(--foreground))] placeholder:text-[rgb(var(--muted-foreground))] focus:outline-none focus:ring-2 focus:ring-obsidian-500/20"
              />
            </div>
          </div>

          {/* Folder tree */}
          <div className="overflow-y-auto max-h-56 p-1">
            {Array.from(folderTree.children.values()).map((node) => (
              <FolderTreeNode
                key={node.path}
                node={node}
                level={0}
                selectedFolders={selectedFolders}
                onToggle={toggleFolder}
                expandedPaths={expandedPaths}
                onToggleExpand={toggleExpand}
                searchTerm={searchTerm}
              />
            ))}
          </div>

          {/* Footer */}
          <div className="p-2 border-t border-[rgb(var(--border))] flex items-center justify-between">
            <div className="flex items-center gap-2">
              {onRefresh && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onRefresh();
                  }}
                  disabled={isRefreshing}
                  className="flex items-center gap-1 text-xs text-[rgb(var(--muted-foreground))] hover:text-obsidian-600 dark:hover:text-obsidian-400 transition-colors"
                  title="Refresh folder list"
                >
                  <RefreshCw className={`h-3 w-3 ${isRefreshing ? "animate-spin" : ""}`} />
                  {isRefreshing ? "Refreshing..." : "Refresh"}
                </button>
              )}
              {selectedFolders.length > 0 && onRefresh && (
                <span className="text-[rgb(var(--border))]">•</span>
              )}
              {selectedFolders.length > 0 && (
                <span className="text-xs text-[rgb(var(--muted-foreground))]">
                  {selectedFolders.length} selected
                </span>
              )}
            </div>
            {selectedFolders.length > 0 && (
              <button
                type="button"
                onClick={clearAll}
                className="text-xs text-obsidian-600 dark:text-obsidian-400 hover:underline"
              >
                Clear all
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
