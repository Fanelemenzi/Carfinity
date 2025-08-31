# Requirements Document

## Introduction

This feature implements a comprehensive scoring system for initial vehicle inspections (160-point inspections) that matches the functionality and approach of the existing quarterly inspection scoring system. The system will calculate vehicle health indices, determine inspection results, generate recommendations, and provide comprehensive scoring analytics for second-hand vehicle evaluations.

## Requirements

### Requirement 1

**User Story:** As a technician, I want the initial inspection system to automatically calculate a vehicle health index based on my inspection results, so that I can provide accurate assessments of second-hand vehicles.

#### Acceptance Criteria

1. WHEN an initial inspection form is completed THEN the system SHALL calculate a health index percentage based on weighted scoring
2. WHEN the health index is calculated THEN the system SHALL categorize it as Excellent (90-100%), Good (80-89%), Fair (70-79%), Poor (60-69%), or Critical (<60%)
3. WHEN critical safety systems fail THEN the system SHALL apply higher weight penalties to the overall score
4. WHEN minor systems have issues THEN the system SHALL apply proportional scoring reductions

### Requirement 2

**User Story:** As a technician, I want the system to automatically determine the inspection result based on the findings, so that I can provide standardized assessments following industry standards.

#### Acceptance Criteria

1. WHEN critical safety systems have major failures THEN the system SHALL mark the inspection as "Failed" (FAI)
2. WHEN there are multiple major defects in critical systems THEN the system SHALL mark as "Failed due to major Defects" (FJD)
3. WHEN there are minor defects only THEN the system SHALL mark as "Passed with minor Defects" (PMD)
4. WHEN no significant issues are found THEN the system SHALL mark as "Passed" (PAS)
5. WHEN the overall health score is below 50% THEN the system SHALL override to "Failed" regardless of individual failures

### Requirement 3

**User Story:** As a technician, I want the system to generate specific maintenance recommendations based on inspection findings, so that I can provide actionable guidance to vehicle owners or buyers.

#### Acceptance Criteria

1. WHEN inspection points fail THEN the system SHALL generate specific recommendations for each failed component
2. WHEN critical safety systems fail THEN the system SHALL mark recommendations as "URGENT"
3. WHEN multiple systems have issues THEN the system SHALL recommend comprehensive vehicle service
4. WHEN no issues are found THEN the system SHALL recommend continuing regular maintenance schedule

### Requirement 4

**User Story:** As a system administrator, I want the initial inspection scoring to integrate seamlessly with the existing inspection workflow, so that technicians have a consistent experience across all inspection types.

#### Acceptance Criteria

1. WHEN an initial inspection form is saved THEN the system SHALL automatically calculate and store the health index
2. WHEN the inspection is marked as completed THEN the system SHALL update all related scoring fields
3. WHEN viewing inspection lists THEN the system SHALL display health indices and completion status consistently
4. WHEN generating reports THEN the system SHALL include comprehensive scoring analytics

### Requirement 5

**User Story:** As a technician, I want to see detailed scoring breakdowns and analytics for initial inspections, so that I can understand how the overall assessment was calculated.

#### Acceptance Criteria

1. WHEN viewing an inspection THEN the system SHALL display the completion percentage
2. WHEN viewing an inspection THEN the system SHALL show the count of failed points by category
3. WHEN viewing an inspection THEN the system SHALL list all failed inspection points with descriptions
4. WHEN viewing an inspection THEN the system SHALL show whether major issues were detected

### Requirement 6

**User Story:** As a vehicle dealer or buyer, I want to receive comprehensive inspection summaries with clear health assessments, so that I can make informed decisions about vehicle purchases.

#### Acceptance Criteria

1. WHEN an inspection is completed THEN the system SHALL generate a comprehensive summary report
2. WHEN generating summaries THEN the system SHALL include health index, inspection result, and recommendations
3. WHEN generating summaries THEN the system SHALL include technician information and inspection metadata
4. WHEN generating summaries THEN the system SHALL provide clear explanations of the scoring methodology