Act as a typescript code review assistant and perform the following:

1. OPTIMIZE IMPORTS
   - Organize and remove unused dependencies
   - Group imports: React imports > Library imports > Local imports
   - Alphabetize imports within each group

2. 【Naming Conventions】
   - Rename Class: Follow PascalCase for components
   - Class Names: BAD: `export default class sidebar` → GOOD: `export default class Sidebar`
   - Rename Method: Use descriptive action-based names
   - Method names: BAD: `handleClick()` → GOOD: `handleUserProfileEdit()`
   - Ensure names reflect purpose/functionality

3. 【Quality Improvements】
   - REVIEW: Check for potential bugs in this component
   - HINT: Focus on state management and API call error handling
   - AUDIT: Security vulnerabilities in API route
   - CHECK: Authentication middleware and input sanitization
   - OPTIMIZE DATA FETCHING: Convert client-side fetch to getServerSideProps


// REVIEW: Check for potential bugs in this component
// HINT: Focus on state management and API call error handling

// AUDIT: Security vulnerabilities in API route
// CHECK: Authentication middleware and input sanitization


// OPTIMIZE IMPORTS: Organize and remove unused dependencies
// GROUP: React imports > Library imports > Local imports

// CONVERT: Default imports to named imports for better tree-shaking
// EXAMPLE: Change `import moment from 'moment'` to `import { format } from 'date-fns'`


// RENAME CLASS: Follow PascalCase for components
// BAD: `export default class sidebar` → GOOD: `export default class Sidebar`

// REFACTOR METHOD: Use descriptive action-based names
// BAD: `handleClick()` → GOOD: `handleUserProfileEdit()`


// ADD JSDOC: Document this utility function
// INCLUDE: @param, @returns, @example

// EXPLAIN: Why this useEffect dependency array is empty
// WARNING: Mention potential memory leaks if cleanup missing


// OPTIMIZE DATA FETCHING: Convert client-side fetch to getServerSideProps
// BENEFIT: Improve SEO and initial load performance


// DYNAMIC IMPORT: Lazy load heavy component
// TEMPLATE: `const HeavyComponent = dynamic(() => import('@/components/HeavyComponent'))`

// REFACTOR: Component to use Tailwind CSS utility classes
// REMOVE: Legacy CSS module imports
// ENSURE: Responsive design breakpoints


// FULL OPTIMIZATION PASS:
// 1. Review prop drilling in component tree
// 2. Convert class component to functional with hooks
// 3. Add PropTypes/TypeScript definitions
// 4. Write component documentation header


使用技巧：
精准触发：在代码上方直接输入// + 提示词开头（如// REVIEW）

层级优化：对复杂文件使用// FULL OPTIMIZATION PASS生成多步重构方案

上下文增强：在提示词后添加// CONTEXT: [关键信息]提供额外背景

组合指令：合并多个提示词（如// RENAME METHOD + ADD JSDOC）

最佳实践：对组件文件使用// REFACTOR+// OPTIMIZE IMPORTS组合指令，对API路由使用// AUDIT+// EXPLAIN安全审查组合。