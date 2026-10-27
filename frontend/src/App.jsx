import { useState } from 'react'
import './App.css'

const API_BASE = 'http://127.0.0.1:8000'

const CATEGORIES = [
  'COD', 'DSA', 'OOD', 'APTI', 'COMM', 'AI', 'CLOUD',
  'SQL', 'SWE', 'SYSD', 'NETW', 'OS', 'OTHER',
]

function App() {
  const [inputMode, setInputMode] = useState('paste')
  const [file, setFile] = useState(null)
  const [text, setText] = useState('')
  const [sourceFile, setSourceFile] = useState('jd_a.txt')
  const [hostedConsent, setHostedConsent] = useState(false)
  const [extraction, setExtraction] = useState(null)
  const [loading, setLoading] = useState(false)
  const [savingReview, setSavingReview] = useState(false)
  const [error, setError] = useState('')

  async function handleExtract(event) {
    event.preventDefault()
    setError('')
    setExtraction(null)

    if (inputMode === 'upload' && !file) {
      setError('Choose a PDF or DOCX file first.')
      return
    }

    if (inputMode === 'paste' && text.trim().length < 15) {
      setError('Paste at least 15 characters of job-description text.')
      return
    }

    setLoading(true)

    try {
      let response

      if (inputMode === 'upload') {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('hosted_consent', String(hostedConsent))

        response = await fetch(`${API_BASE}/api/team/v1/jd/extract`, {
          method: 'POST',
          body: formData,
        })
      } else {
        response = await fetch(`${API_BASE}/api/team/v1/jd/extract-text`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text,
            source_file: sourceFile,
            hosted_consent: hostedConsent,
          }),
        })
      }

      const result = await response.json()

      if (!response.ok) {
        throw new Error(
          result?.error?.message || 'The extraction request could not be completed.',
        )
      }

      setExtraction(result)
    } catch (requestError) {
      setError(
        requestError.message ||
          'Could not reach the backend. Check that it is running on port 8000.',
      )
    } finally {
      setLoading(false)
    }
  }

  async function handleReviewAndSave() {
    if (!extraction) return

    setError('')
    setSavingReview(true)

    try {
      const response = await fetch(`${API_BASE}/api/team/v1/jd/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(extraction),
      })

      const result = await response.json()

      if (!response.ok) {
        throw new Error(
          result?.error?.message || 'The review could not be saved.',
        )
      }

      setExtraction(result)
    } catch (requestError) {
      setError(
        requestError.message ||
          'Could not reach the backend. Check that it is running on port 8000.',
      )
    } finally {
      setSavingReview(false)
    }
  }

  function updateExtraction(field, value) {
    setExtraction((current) => ({ ...current, [field]: value }))
  }

  function updateSkill(skillId, field, value) {
    setExtraction((current) => ({
      ...current,
      skills: current.skills.map((skill) =>
        skill.skill_id === skillId ? { ...skill, [field]: value } : skill,
      ),
    }))
  }

  function updateGroup(requirementId, field, value) {
    setExtraction((current) => ({
      ...current,
      requirement_groups: current.requirement_groups.map((group) =>
        group.requirement_id === requirementId
          ? { ...group, [field]: value }
          : group,
      ),
    }))
  }

  function toggleGroupSkill(requirementId, skillId, shouldInclude) {
    const group = extraction.requirement_groups.find(
      (item) => item.requirement_id === requirementId,
    )
    if (!group) return

    const skillIds = shouldInclude
      ? [...new Set([...group.skill_ids, skillId])]
      : group.skill_ids.filter((id) => id !== skillId)

    // TEAM-V1 requires at least one skill in every requirement group.
    if (skillIds.length > 0) {
      updateGroup(requirementId, 'skill_ids', skillIds)
    }
  }

  function getSkillName(skillId) {
    return (
      extraction?.skills.find((skill) => skill.skill_id === skillId)?.skill_name ||
      'Unknown skill'
    )
  }

  function downloadReviewedJson() {
    const json = JSON.stringify(extraction, null, 2)
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')

    link.href = url
    link.download = `${extraction.id}-reviewed.json`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  }

  function changeInputMode(mode) {
    setInputMode(mode)
    setExtraction(null)
    setError('')
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="RADIX JD Analytics home">
          <span className="brand-mark" aria-hidden="true">R</span>
          <span>RADIX <span className="brand-divider">/</span> JD Analytics</span>
        </a>
        <span className="module-label">MODULE 01</span>
      </header>

      <section className="intro">
        <p className="eyebrow">JOB DESCRIPTION REVIEW</p>
        <h1>Understand what the job asks for.</h1>
        <p className="intro-copy">
          Extract requirements with their source wording, then review them before
          saving a result.
        </p>
      </section>

      <main className="workspace">
        <section className="panel input-panel" aria-labelledby="input-heading">
          <div className="panel-heading">
            <div>
              <p className="step-label">STEP 01</p>
              <h2 id="input-heading">Add a job description</h2>
            </div>
          </div>

          <div className="mode-switch" aria-label="Choose input method">
            <button
              type="button"
              className={inputMode === 'paste' ? 'mode-button active' : 'mode-button'}
              onClick={() => changeInputMode('paste')}
              aria-pressed={inputMode === 'paste'}
            >
              Paste text
            </button>
            <button
              type="button"
              className={inputMode === 'upload' ? 'mode-button active' : 'mode-button'}
              onClick={() => changeInputMode('upload')}
              aria-pressed={inputMode === 'upload'}
            >
              Upload file
            </button>
          </div>

          <form onSubmit={handleExtract}>
            {inputMode === 'paste' ? (
              <>
                <label htmlFor="source-file">Source filename</label>
                <input
                  id="source-file"
                  type="text"
                  value={sourceFile}
                  onChange={(event) => setSourceFile(event.target.value)}
                  placeholder="jd_a.txt"
                  required
                />

                <label htmlFor="jd-text">Job description text</label>
                <textarea
                  id="jd-text"
                  value={text}
                  onChange={(event) => setText(event.target.value)}
                  placeholder={'Company: Synthetic Practice Co\nRole: Junior Developer\nRequired: Python\nPreferred: SQL'}
                  rows={8}
                  minLength={15}
                  maxLength={100000}
                  required
                />
                <p className="field-hint">
                  Keep the original wording so claims can be checked against it.
                </p>
              </>
            ) : (
              <>
                <label htmlFor="jd-file">PDF or Word document</label>
                <input
                  id="jd-file"
                  type="file"
                  accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  onChange={(event) => setFile(event.target.files?.[0] || null)}
                />
                <p className="field-hint">
                  Use a text-based PDF or a DOCX file, up to 10 MB.
                </p>
              </>
            )}

            <label className="consent-row">
              <input
                type="checkbox"
                checked={hostedConsent}
                onChange={(event) => setHostedConsent(event.target.checked)}
              />
              <span>
                I consent to sending this job description to Groq for hosted AI
                extraction.
              </span>
            </label>

            <p className="privacy-note">
              Leave this unchecked to use the offline path. No API key is stored
              or sent by this screen.
            </p>

            {error && (
              <p className="error-message" role="alert">{error}</p>
            )}

            <button className="primary-button" type="submit" disabled={loading}>
              {loading ? 'Extracting…' : 'Extract requirements'}
            </button>
          </form>
        </section>

        <section className="panel result-panel" aria-labelledby="result-heading">
          <div className="panel-heading">
            <div>
              <p className="step-label">STEP 02</p>
              <h2 id="result-heading">Extraction preview</h2>
            </div>
            {extraction && (
              <span className="status-badge">
                {extraction.review_status === 'reviewed'
                  ? 'Reviewed'
                  : 'Needs review'}
              </span>
            )}
          </div>

          {!extraction ? (
            <div className="empty-state" aria-live="polite">
              <span className="empty-icon" aria-hidden="true">↳</span>
              <h3>Your results will appear here</h3>
              <p>
                Add a job description and choose Extract to see its proposed
                skills and requirements.
              </p>
            </div>
          ) : (
            <div className="results" aria-live="polite">
              <div className="metadata">
                <span>
                  Method: <strong>{extraction.extraction_method}</strong>
                </span>
                <span>
                  Source: <strong>{extraction.source_file}</strong>
                </span>
              </div>

              <div className="job-heading">
                <label htmlFor="review-company">Company</label>
                <input
                  id="review-company"
                  value={extraction.company || ''}
                  onChange={(event) => updateExtraction('company', event.target.value)}
                  disabled={extraction.review_status === 'reviewed' || savingReview}
                />
                <label htmlFor="review-role">Role</label>
                <input
                  id="review-role"
                  value={extraction.role || ''}
                  onChange={(event) => updateExtraction('role', event.target.value)}
                  disabled={extraction.review_status === 'reviewed' || savingReview}
                />
              </div>

              <h3 className="section-title">
                Skills <span>{extraction.skills.length}</span>
              </h3>

              {extraction.skills.length === 0 ? (
                <p className="empty-list">
                  No skills were proposed. This is expected on the offline
                  manual path; it does not invent claims.
                </p>
              ) : (
                <div className="skill-list">
                  {extraction.skills.map((skill) => (
                    <article className="skill-card" key={skill.skill_id}>
                      <label htmlFor={`skill-name-${skill.skill_id}`}>Skill</label>
                      <input
                        id={`skill-name-${skill.skill_id}`}
                        value={skill.skill_name}
                        onChange={(event) =>
                          updateSkill(skill.skill_id, 'skill_name', event.target.value)
                        }
                        disabled={extraction.review_status === 'reviewed' || savingReview}
                      />

                      <label htmlFor={`skill-category-${skill.skill_id}`}>Category</label>
                      <select
                        id={`skill-category-${skill.skill_id}`}
                        value={skill.category_code}
                        onChange={(event) =>
                          updateSkill(skill.skill_id, 'category_code', event.target.value)
                        }
                        disabled={extraction.review_status === 'reviewed' || savingReview}
                      >
                        {CATEGORIES.map((category) => (
                          <option key={category} value={category}>{category}</option>
                        ))}
                      </select>

                      <label htmlFor={`skill-evidence-${skill.skill_id}`}>
                        Source evidence — keep this wording in the source text
                      </label>
                      <textarea
                        id={`skill-evidence-${skill.skill_id}`}
                        value={skill.evidence}
                        onChange={(event) =>
                          updateSkill(skill.skill_id, 'evidence', event.target.value)
                        }
                        disabled={extraction.review_status === 'reviewed' || savingReview}
                      />

                      <label htmlFor={`skill-confidence-${skill.skill_id}`}>
                        Confidence
                      </label>
                      <select
                        id={`skill-confidence-${skill.skill_id}`}
                        value={skill.confidence}
                        onChange={(event) =>
                          updateSkill(skill.skill_id, 'confidence', event.target.value)
                        }
                        disabled={extraction.review_status === 'reviewed' || savingReview}
                      >
                        <option value="high">high</option>
                        <option value="medium">medium</option>
                        <option value="low">low</option>
                      </select>

                      <label htmlFor={`skill-claim-${skill.skill_id}`}>
                        Claim status
                      </label>
                      <select
                        id={`skill-claim-${skill.skill_id}`}
                        value={skill.claim_status}
                        onChange={(event) =>
                          updateSkill(skill.skill_id, 'claim_status', event.target.value)
                        }
                        disabled={extraction.review_status === 'reviewed' || savingReview}
                      >
                        <option value="claimed">claimed</option>
                        <option value="needs_review">needs review</option>
                      </select>
                    </article>
                  ))}
                </div>
              )}

              <h3 className="section-title">
                Requirement groups <span>{extraction.requirement_groups.length}</span>
              </h3>

              {extraction.requirement_groups.length === 0 ? (
                <p className="empty-list">No requirement groups were proposed.</p>
              ) : (
                <div className="group-list">
                  {extraction.requirement_groups.map((group) => (
                    <article className="group-card" key={group.requirement_id}>
                      <fieldset
                        className="group-members"
                        disabled={extraction.review_status === 'reviewed' || savingReview}
                      >
                        <legend>Skills in this requirement group</legend>
                        {extraction.skills.map((skill) => {
                          const checked = group.skill_ids.includes(skill.skill_id)

                          return (
                            <label key={skill.skill_id}>
                              <input
                                type="checkbox"
                                checked={checked}
                                disabled={checked && group.skill_ids.length === 1}
                                onChange={(event) =>
                                  toggleGroupSkill(
                                    group.requirement_id,
                                    skill.skill_id,
                                    event.target.checked,
                                  )
                                }
                              />
                              {skill.skill_name}
                            </label>
                          )
                        })}
                      </fieldset>
                      <p>
                        Current group: {group.skill_ids
                          .map(getSkillName)
                          .join(` ${group.operator} `)}
                      </p>

                      <label htmlFor={`group-operator-${group.requirement_id}`}>
                        Operator
                      </label>
                      <select
                        id={`group-operator-${group.requirement_id}`}
                        value={group.operator}
                        onChange={(event) =>
                          updateGroup(group.requirement_id, 'operator', event.target.value)
                        }
                        disabled={extraction.review_status === 'reviewed' || savingReview}
                      >
                        <option value="AND">AND</option>
                        <option value="OR">OR</option>
                      </select>

                      <label htmlFor={`group-type-${group.requirement_id}`}>
                        Requirement type
                      </label>
                      <select
                        id={`group-type-${group.requirement_id}`}
                        value={group.requirement_type}
                        onChange={(event) =>
                          updateGroup(
                            group.requirement_id,
                            'requirement_type',
                            event.target.value,
                          )
                        }
                        disabled={extraction.review_status === 'reviewed' || savingReview}
                      >
                        <option value="mandatory">mandatory</option>
                        <option value="preferred">preferred</option>
                        <option value="unspecified">unspecified</option>
                      </select>

                      <label htmlFor={`group-evidence-${group.requirement_id}`}>
                        Source evidence — keep this wording in the source text
                      </label>
                      <textarea
                        id={`group-evidence-${group.requirement_id}`}
                        value={group.evidence}
                        onChange={(event) =>
                          updateGroup(group.requirement_id, 'evidence', event.target.value)
                        }
                        disabled={extraction.review_status === 'reviewed' || savingReview}
                      />
                    </article>
                  ))}
                </div>
              )}

              {extraction.warnings.length > 0 && (
                <div className="warning-box">
                  <h3>Warnings</h3>
                  <ul>
                    {extraction.warnings.map((warning, index) => (
                      <li key={`${index}-${warning}`}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}

              <details className="source-details">
                <summary>View extracted source text</summary>
                <pre>{extraction.source_text}</pre>
              </details>

              {extraction.review_status !== 'reviewed' ? (
                <button
                  className="primary-button"
                  type="button"
                  onClick={handleReviewAndSave}
                  disabled={savingReview}
                >
                  {savingReview ? 'Saving review…' : 'Review and save'}
                </button>
              ) : (
                <button
                  className="primary-button"
                  type="button"
                  onClick={downloadReviewedJson}
                >
                  Download reviewed JSON
                </button>
              )}
            </div>
          )}
        </section>
      </main>

      <footer className="footer">
        <span>RADIX · TEAM-V1</span>
        <span>Review every claim before exporting.</span>
      </footer>
    </main>
  )
}

export default App
