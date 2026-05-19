package com.gisma.career.service;

import com.gisma.career.dto.JobResponse;
import com.gisma.career.model.Job;
import com.gisma.career.model.Skill;
import com.gisma.career.model.Student;
import com.gisma.career.repository.JobRepository;
import org.springframework.stereotype.Service;

import java.util.Comparator;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

@Service
public class JobRecommendationService {

    private final JobRepository jobRepository;

    public JobRecommendationService(JobRepository jobRepository) {
        this.jobRepository = jobRepository;
    }

    /**
     * Simple recommendation: percent of required skills the student has.
     * Optional job type filter ("all", "internship", "fulltime", "parttime", "remote").
     */
    public List<JobResponse> recommendFor(Student student, String filter) {
        Set<String> studentSkillNames = student.getSkills().stream()
                .map(s -> s.getName().toLowerCase())
                .collect(Collectors.toSet());

        List<JobResponse> results = jobRepository.findAll().stream()
                .filter(job -> matchesFilter(job, filter))
                .map(job -> toResponse(job, studentSkillNames))
                .sorted(Comparator.comparingInt(JobResponse::getMatchPercent).reversed())
                .collect(Collectors.toList());
        return results;
    }

    private boolean matchesFilter(Job job, String filter) {
        if (filter == null || filter.isBlank() || filter.equalsIgnoreCase("all")) return true;
        return job.getJobType() != null && job.getJobType().equalsIgnoreCase(filter);
    }

    private JobResponse toResponse(Job job, Set<String> studentSkillNames) {
        List<String> required = job.getRequiredSkills().stream()
                .map(Skill::getName)
                .collect(Collectors.toList());

        int matchPct = 0;
        if (!required.isEmpty()) {
            long matched = required.stream()
                    .filter(s -> studentSkillNames.contains(s.toLowerCase()))
                    .count();
            matchPct = (int) Math.round(100.0 * matched / required.size());
        }

        return new JobResponse(
                job.getId(),
                job.getTitle(),
                job.getCompany(),
                job.getLocation(),
                job.getJobType(),
                job.getSalary(),
                job.getPostedDate(),
                required,
                matchPct
        );
    }
}
