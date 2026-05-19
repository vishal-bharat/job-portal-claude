package com.gisma.career.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.time.LocalDate;
import java.util.List;

@Data
@AllArgsConstructor
public class JobResponse {
    private Long id;
    private String title;
    private String company;
    private String location;
    private String jobType;
    private String salary;
    private LocalDate postedDate;
    private List<String> requiredSkills;
    private int matchPercent;
}
