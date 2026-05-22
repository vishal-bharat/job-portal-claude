package com.gisma.career.service;

import com.gisma.career.dto.JobResponse;
import com.gisma.career.model.Job;
import com.gisma.career.model.Skill;
import com.gisma.career.model.Student;
import com.gisma.career.repository.JobRepository;
import org.springframework.stereotype.Service;

import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * Content-based job recommendation.
 *
 * Each job and each student is turned into a TF-IDF weighted vector over the
 * skill vocabulary, and jobs are ranked by COSINE SIMILARITY to the student.
 *
 * Why TF-IDF + cosine instead of a plain overlap count:
 *  - IDF (inverse document frequency) makes rare, distinctive skills count more
 *    than common ones. Matching "Kubernetes" (few jobs need it) is worth more
 *    than matching "SQL" (almost every job needs it).
 *  - Cosine similarity normalises by vector length, so a job is not unfairly
 *    penalised just for requiring many skills.
 *
 * This is a non-parametric, instance-based method: there is no training step,
 * and the scores are recomputed on every request, so adding or removing a skill
 * updates the recommendations immediately.
 */
@Service
public class JobRecommendationService {

    private final JobRepository jobRepository;

    public JobRecommendationService(JobRepository jobRepository) {
        this.jobRepository = jobRepository;
    }

    /**
     * Recommend jobs for a student, ranked by cosine similarity (highest first).
     * Optional job type filter ("all", "internship", "fulltime", "parttime", "remote").
     */
    public List<JobResponse> recommendFor(Student student, String filter) {
        List<Job> allJobs = jobRepository.findAll();

        // 1. IDF is a property of the whole job corpus, so compute it from ALL
        //    jobs - not just the filtered subset - to keep weights stable.
        Map<String, Double> idf = computeIdf(allJobs);

        // 2. The student's skill set (lower-cased for case-insensitive matching).
        Set<String> studentSkills = student.getSkills().stream()
                .map(s -> s.getName().toLowerCase())
                .collect(Collectors.toSet());

        // 3. The student's vector length is the same for every job, so compute once.
        double studentNorm = vectorNorm(studentSkills, idf);

        // 4. Score every job, apply the filter, and sort by match descending.
        return allJobs.stream()
                .filter(job -> matchesFilter(job, filter))
                .map(job -> toResponse(job, studentSkills, idf, studentNorm))
                .sorted(Comparator.comparingInt(JobResponse::getMatchPercent).reversed())
                .collect(Collectors.toList());
    }

    /**
     * Inverse document frequency for every skill in the corpus.
     *
     * Jobs are the "documents"; a job's required skills are its "terms".
     * Smoothed formula (scikit-learn style):
     *
     *     idf(skill) = ln( (1 + N) / (1 + df) ) + 1
     *
     * where N  = total number of jobs,
     *       df = number of jobs that require this skill.
     *
     * Rare skills -> high idf; common skills -> low idf. The "+1" keeps every
     * weight positive so no skill is ever zeroed out completely.
     */
    private Map<String, Double> computeIdf(List<Job> jobs) {
        int n = jobs.size();
        Map<String, Integer> docFrequency = new HashMap<>();

        for (Job job : jobs) {
            // distinct skills of this job (a job lists each skill at most once)
            Set<String> skills = job.getRequiredSkills().stream()
                    .map(s -> s.getName().toLowerCase())
                    .collect(Collectors.toSet());
            for (String skill : skills) {
                docFrequency.merge(skill, 1, Integer::sum);
            }
        }

        Map<String, Double> idf = new HashMap<>();
        for (Map.Entry<String, Integer> entry : docFrequency.entrySet()) {
            double value = Math.log((1.0 + n) / (1.0 + entry.getValue())) + 1.0;
            idf.put(entry.getKey(), value);
        }
        return idf;
    }

    /**
     * Euclidean length (magnitude) of a skill set's TF-IDF vector.
     * Term frequency is 1 for every skill present, so each vector component is
     * simply idf(skill). Skills not seen in the corpus are ignored.
     *
     *     ||v|| = sqrt( sum of idf(skill)^2 )
     */
    private double vectorNorm(Set<String> skills, Map<String, Double> idf) {
        double sumOfSquares = 0.0;
        for (String skill : skills) {
            Double weight = idf.get(skill);
            if (weight != null) {
                sumOfSquares += weight * weight;
            }
        }
        return Math.sqrt(sumOfSquares);
    }

    private boolean matchesFilter(Job job, String filter) {
        if (filter == null || filter.isBlank() || filter.equalsIgnoreCase("all")) {
            return true;
        }
        return job.getJobType() != null && job.getJobType().equalsIgnoreCase(filter);
    }

    private JobResponse toResponse(Job job, Set<String> studentSkills,
                                   Map<String, Double> idf, double studentNorm) {
        List<String> required = job.getRequiredSkills().stream()
                .map(Skill::getName)
                .collect(Collectors.toList());

        Set<String> jobSkills = required.stream()
                .map(String::toLowerCase)
                .collect(Collectors.toSet());

        int matchPct = cosineSimilarityPercent(studentSkills, studentNorm, jobSkills, idf);

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

    /**
     * Cosine similarity between the student vector and the job vector,
     * returned as a 0-100 percentage.
     *
     *                    dot(student, job)
     *     cosine = -----------------------------------
     *                  ||student|| * ||job||
     *
     * Both vectors use TF-IDF weights and TF = 1, so a vector component is
     * idf(skill). For a skill shared by student AND job, its contribution to
     * the dot product is idf(skill) * idf(skill) = idf(skill)^2.
     *
     * Cosine of two non-negative vectors is always in [0, 1], so the percentage
     * is naturally bounded between 0 and 100.
     */
    private int cosineSimilarityPercent(Set<String> studentSkills, double studentNorm,
                                        Set<String> jobSkills, Map<String, Double> idf) {
        double jobNorm = vectorNorm(jobSkills, idf);

        // If either side has no (known) skills, similarity is undefined -> 0.
        if (studentNorm == 0.0 || jobNorm == 0.0) {
            return 0;
        }

        double dotProduct = 0.0;
        for (String skill : jobSkills) {
            if (studentSkills.contains(skill)) {
                Double weight = idf.get(skill);
                if (weight != null) {
                    dotProduct += weight * weight;
                }
            }
        }

        double cosine = dotProduct / (studentNorm * jobNorm);
        return (int) Math.round(cosine * 100.0);
    }
}
